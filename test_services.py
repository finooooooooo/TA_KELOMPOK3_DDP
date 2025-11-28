import unittest
from unittest.mock import MagicMock, call
from decimal import Decimal
import services

class TestPOS(unittest.TestCase):
    def setUp(self):
        self.mock_conn = MagicMock()
        self.mock_cursor = MagicMock()
        self.mock_conn.cursor.return_value = self.mock_cursor

    def test_process_order_success(self):
        # Mock product fetch
        # Product: id=1, name='Water', price=2.00, managed=True, stock=10, active=True
        self.mock_cursor.fetchone.side_effect = [
            {'name': 'Water', 'price': 2.00, 'is_inventory_managed': True, 'stock_quantity': 10, 'is_active': True},
            {'id': 101} # Return order ID
        ]

        cart = [{'product_id': 1, 'quantity': 2}]
        # Subtotal: 4.00, Tax: 0.40, Total: 4.40

        order_id = services.process_order(
            self.mock_conn, 1, 'TRX-001', 'cash', Decimal('10.00'), cart
        )

        # Check commits
        self.mock_conn.commit.assert_called_once()

        # Verify calls
        # 1. Select Product
        # 2. Update Stock
        # 3. Insert Order
        # 4. Insert Order Items

        # Verify Stock Deduction
        self.mock_cursor.execute.assert_any_call(
            "UPDATE products SET stock_quantity = %s WHERE id = %s", (8, 1)
        )

        # Verify Order Insert (Check Total and Tax)
        # We need to find the call to INSERT INTO orders
        insert_order_call = [call for call in self.mock_cursor.execute.call_args_list if "INSERT INTO orders" in call[0][0]]
        self.assertTrue(insert_order_call)

        args = insert_order_call[0][0][1]
        # args: (user_id, trx, total, tax, method, received, change)
        total_amount = args[2]
        tax_amount = args[3]

        self.assertEqual(total_amount, Decimal('4.40')) # 4.00 + 10%
        self.assertEqual(tax_amount, Decimal('0.40'))

    def test_process_order_insufficient_stock(self):
        # Product: Stock=10, Request=11
        self.mock_cursor.fetchone.return_value = {
            'name': 'Water', 'price': 2.00, 'is_inventory_managed': True, 'stock_quantity': 10, 'is_active': True
        }

        cart = [{'product_id': 1, 'quantity': 11}]

        with self.assertRaises(Exception) as cm:
            services.process_order(
                self.mock_conn, 1, 'TRX-FAIL', 'cash', Decimal('100.00'), cart
            )

        self.assertIn('Insufficient stock', str(cm.exception))
        self.mock_conn.rollback.assert_called_once()

    def test_void_order_restock(self):
        # 1. Get Order (status='paid')
        # 2. Get Items (qty=5, managed=True)
        # 3. Update Product Stock (+5)
        # 4. Update Order Status

        self.mock_cursor.fetchone.side_effect = [
            {'status': 'paid'}, # Order fetch
            # No fetchone for items, it uses fetchall
        ]

        self.mock_cursor.fetchall.return_value = [
            {'product_id': 1, 'quantity': 5, 'is_inventory_managed': True}
        ]

        services.void_order(self.mock_conn, 101, 1)

        # Verify Restock
        self.mock_cursor.execute.assert_any_call(
            "UPDATE products SET stock_quantity = stock_quantity + %s WHERE id = %s",
            (5, 1)
        )

        # Verify Status Update
        self.assertTrue(any("UPDATE orders SET status = 'cancelled'" in str(c) for c in self.mock_cursor.execute.call_args_list))
        self.mock_conn.commit.assert_called_once()

if __name__ == '__main__':
    unittest.main()
