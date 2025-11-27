import unittest
import sqlite3
import os
from decimal import Decimal
import services

class TestPOS(unittest.TestCase):
    def setUp(self):
        self.db_name = 'test_coffee.sqlite'
        # Setup clean DB
        if os.path.exists(self.db_name):
            os.remove(self.db_name)

        self.conn = sqlite3.connect(self.db_name)
        self.conn.row_factory = sqlite3.Row  # Fix: Enable Row factory
        with open('schema.sql', 'r') as f:
            self.conn.executescript(f.read())

        self.cursor = self.conn.cursor()

        # Seed test data
        self.cursor.execute("INSERT INTO roles (name) VALUES ('admin'), ('cashier')")
        self.cursor.execute("INSERT INTO users (role_id, username, password_hash) VALUES (2, 'cashier', 'hash')")
        self.cursor.execute("INSERT INTO categories (name) VALUES ('Drinks')")

        # Product 1: Managed, Stock 10
        self.cursor.execute("""
            INSERT INTO products (category_id, name, price, is_inventory_managed, stock_quantity)
            VALUES (1, 'Water', 2.00, 1, 10)
        """)
        # Product 2: Unmanaged
        self.cursor.execute("""
            INSERT INTO products (category_id, name, price, is_inventory_managed, stock_quantity)
            VALUES (1, 'Service', 10.00, 0, 0)
        """)
        self.conn.commit()

    def tearDown(self):
        self.conn.close()
        if os.path.exists(self.db_name):
            os.remove(self.db_name)

    def test_atomic_order_success(self):
        cart = [{'product_id': 1, 'quantity': 2}] # Buy 2 Water
        order_id = services.process_order(
            self.conn, 1, 'TRX-001', 'cash', Decimal('5.00'), cart
        )

        # Check Order
        self.cursor.execute("SELECT total_amount FROM orders WHERE id=?", (order_id,))
        self.assertEqual(self.cursor.fetchone()[0], 4.00)

        # Check Stock Deducted (10 - 2 = 8)
        self.cursor.execute("SELECT stock_quantity FROM products WHERE id=1")
        self.assertEqual(self.cursor.fetchone()[0], 8)

    def test_atomic_order_insufficient_stock(self):
        cart = [{'product_id': 1, 'quantity': 11}] # Buy 11 Water (Stock 10)

        with self.assertRaises(Exception) as cm:
            services.process_order(
                self.conn, 1, 'TRX-FAIL', 'cash', Decimal('100.00'), cart
            )
        self.assertIn('Insufficient stock', str(cm.exception))

        # Check Stock Unchanged
        self.cursor.execute("SELECT stock_quantity FROM products WHERE id=1")
        self.assertEqual(self.cursor.fetchone()[0], 10)

    def test_snapshot_pricing(self):
        # Buy Water at 2.00
        cart = [{'product_id': 1, 'quantity': 1}]
        order_id = services.process_order(self.conn, 1, 'TRX-SNAP', 'cash', Decimal('10.00'), cart)

        # Change Product Price to 5.00
        self.cursor.execute("UPDATE products SET price = 5.00 WHERE id = 1")
        self.conn.commit()

        # Check Order Item Snapshot
        self.cursor.execute("SELECT price_snapshot FROM order_items WHERE order_id=?", (order_id,))
        snapshot_price = self.cursor.fetchone()[0]
        self.assertEqual(snapshot_price, 2.00)

    def test_void_restock(self):
        # Buy 5 Water (Stock 10 -> 5)
        cart = [{'product_id': 1, 'quantity': 5}]
        order_id = services.process_order(self.conn, 1, 'TRX-VOID', 'cash', Decimal('20.00'), cart)

        self.cursor.execute("SELECT stock_quantity FROM products WHERE id=1")
        self.assertEqual(self.cursor.fetchone()[0], 5)

        # Void Order
        services.void_order(self.conn, order_id, 1)

        # Check Status
        self.cursor.execute("SELECT status, voided_by FROM orders WHERE id=?", (order_id,))
        row = self.cursor.fetchone()
        self.assertEqual(row[0], 'cancelled')
        self.assertEqual(row[1], 1)

        # Check Restock (5 -> 10)
        self.cursor.execute("SELECT stock_quantity FROM products WHERE id=1")
        self.assertEqual(self.cursor.fetchone()[0], 10)

if __name__ == '__main__':
    unittest.main()
