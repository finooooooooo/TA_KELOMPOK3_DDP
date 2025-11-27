import sqlite3
import datetime
from decimal import Decimal

def process_order(db_conn, user_id, transaction_code, payment_method, amount_received, cart_items):
    """
    Atomic transaction to process an order.

    Args:
        db_conn: SQLite connection object (must support rollback/commit)
        user_id: ID of the cashier/user
        transaction_code: Unique code for transaction
        payment_method: 'cash' or 'qris'
        amount_received: Decimal amount
        cart_items: List of dicts {'product_id': int, 'quantity': int}

    Returns:
        order_id on success, raises Exception on failure.
    """
    cursor = db_conn.cursor()

    try:
        # Calculate totals and validate stock first
        total_amount = Decimal('0.00')
        final_items = []

        for item in cart_items:
            product_id = item['product_id']
            qty = item['quantity']

            # Fetch current product state
            cursor.execute(
                "SELECT name, price, is_inventory_managed, stock_quantity, is_active FROM products WHERE id = ?",
                (product_id,)
            )
            product = cursor.fetchone()

            if not product:
                raise Exception(f"Product ID {product_id} not found.")

            if not product['is_active']:
                raise Exception(f"Product {product['name']} is inactive.")

            # Check Stock
            if product['is_inventory_managed']:
                if product['stock_quantity'] < qty:
                    raise Exception(f"Insufficient stock for {product['name']}. Available: {product['stock_quantity']}")

                # Deduct Stock
                new_stock = product['stock_quantity'] - qty
                cursor.execute("UPDATE products SET stock_quantity = ? WHERE id = ?", (new_stock, product_id))

            # Snapshot data
            price = Decimal(str(product['price']))
            subtotal = price * qty
            total_amount += subtotal

            final_items.append({
                'product_id': product_id,
                'name_snapshot': product['name'],
                'price_snapshot': price,
                'quantity': qty,
                'subtotal': subtotal
            })

        # Create Order Header
        change_amount = Decimal(amount_received) - total_amount
        if change_amount < 0:
             raise Exception(f"Insufficient payment. Total: {total_amount}, Received: {amount_received}")

        cursor.execute(
            """INSERT INTO orders (user_id, transaction_code, total_amount, payment_method, amount_received, change_amount)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (user_id, transaction_code, str(total_amount), payment_method, str(amount_received), str(change_amount))
        )
        order_id = cursor.lastrowid

        # Create Order Items
        for item in final_items:
            cursor.execute(
                """INSERT INTO order_items (order_id, product_id, product_name_snapshot, price_snapshot, quantity, subtotal)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (order_id, item['product_id'], item['name_snapshot'], str(item['price_snapshot']), item['quantity'], str(item['subtotal']))
            )

        db_conn.commit()
        return order_id

    except Exception as e:
        db_conn.rollback()
        raise e

def void_order(db_conn, order_id, user_id):
    """
    Void an order and restock inventory if applicable.
    """
    cursor = db_conn.cursor()

    try:
        # Get order status
        cursor.execute("SELECT status FROM orders WHERE id = ?", (order_id,))
        order = cursor.fetchone()

        if not order:
             raise Exception("Order not found")

        if order['status'] == 'cancelled':
            raise Exception("Order is already cancelled")

        # Get Order Items
        cursor.execute("""
            SELECT oi.product_id, oi.quantity, p.is_inventory_managed
            FROM order_items oi
            JOIN products p ON oi.product_id = p.id
            WHERE oi.order_id = ?
        """, (order_id,))

        items = cursor.fetchall()

        # Restock
        for item in items:
            if item['is_inventory_managed']:
                cursor.execute(
                    "UPDATE products SET stock_quantity = stock_quantity + ? WHERE id = ?",
                    (item['quantity'], item['product_id'])
                )

        # Update Order Status
        now = datetime.datetime.now()
        cursor.execute(
            "UPDATE orders SET status = 'cancelled', voided_by = ?, voided_at = ? WHERE id = ?",
            (user_id, now, order_id)
        )

        db_conn.commit()
        return True

    except Exception as e:
        db_conn.rollback()
        raise e
