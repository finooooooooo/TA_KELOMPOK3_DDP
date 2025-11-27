import unittest
import os
import json
from app import create_app
import sqlite3

class TestAPI(unittest.TestCase):
    def setUp(self):
        self.db_path = 'test_coffee_api.sqlite'
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

        self.app = create_app({
            'TESTING': True,
            'DATABASE': self.db_path
        })
        self.client = self.app.test_client()

        with self.app.app_context():
            from db import init_db
            init_db()
            db = sqlite3.connect(self.db_path)
            cursor = db.cursor()

            # Seed Roles and Users
            cursor.execute("INSERT INTO roles (name) VALUES ('admin'), ('cashier')")
            # Password hashes using 'werkzeug.security.generate_password_hash'
            # admin/admin123, cashier/cashier123
            from werkzeug.security import generate_password_hash
            cursor.execute("INSERT INTO users (role_id, username, password_hash) VALUES (1, 'admin', ?)",
                           (generate_password_hash('admin123'),))
            cursor.execute("INSERT INTO users (role_id, username, password_hash) VALUES (2, 'cashier', ?)",
                           (generate_password_hash('cashier123'),))

            # Seed Products
            cursor.execute("INSERT INTO categories (name) VALUES ('Drinks')")
            cursor.execute("""
                INSERT INTO products (category_id, name, price, is_inventory_managed, stock_quantity)
                VALUES (1, 'Test Coffee', 3.50, 0, 0)
            """)
            cursor.execute("""
                INSERT INTO products (category_id, name, price, is_inventory_managed, stock_quantity)
                VALUES (1, 'Test Water', 1.00, 1, 10)
            """)
            db.commit()
            db.close()

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def login(self, username, password):
        return self.client.post('/auth/login', data=dict(
            username=username,
            password=password
        ), follow_redirects=True)

    def test_login_session(self):
        response = self.login('cashier', 'cashier123')
        self.assertEqual(response.status_code, 200)
        with self.client.session_transaction() as sess:
            self.assertEqual(sess['role_name'], 'cashier')

    def test_unauthorized_access(self):
        # Try accessing API without login
        response = self.client.get('/api/products')
        self.assertEqual(response.status_code, 302) # Redirects to login
        self.assertIn('/auth/login', response.headers['Location'])

    def test_get_products(self):
        self.login('cashier', 'cashier123')
        response = self.client.get('/api/products')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('products', data)
        self.assertEqual(len(data['products']), 2)
        self.assertEqual(data['products'][0]['name'], 'Test Coffee')

    def test_create_order_success(self):
        self.login('cashier', 'cashier123')

        payload = {
            'cart': [
                {'product_id': 1, 'quantity': 1}, # Coffee 3.50
                {'product_id': 2, 'quantity': 2}  # Water 1.00 * 2 = 2.00
            ],
            'payment_method': 'cash',
            'amount_received': 10.00
        }

        response = self.client.post('/api/orders',
                                    data=json.dumps(payload),
                                    content_type='application/json')

        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertIn('transaction_code', data)

    def test_create_order_insufficient_stock_api(self):
        self.login('cashier', 'cashier123')

        payload = {
            'cart': [
                {'product_id': 2, 'quantity': 20} # Water Stock 10
            ],
            'payment_method': 'cash',
            'amount_received': 100.00
        }

        response = self.client.post('/api/orders',
                                    data=json.dumps(payload),
                                    content_type='application/json')

        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('Insufficient stock', data['error'])

    def test_admin_access_control(self):
        # Cashier trying to access admin dashboard
        self.login('cashier', 'cashier123')
        response = self.client.get('/admin/dashboard')
        self.assertEqual(response.status_code, 403)

        # Admin accessing admin dashboard
        self.login('admin', 'admin123')
        response = self.client.get('/admin/dashboard')
        self.assertEqual(response.status_code, 200)

if __name__ == '__main__':
    unittest.main()
