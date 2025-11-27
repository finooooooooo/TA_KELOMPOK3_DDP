import sqlite3
import os
from werkzeug.security import generate_password_hash

DATABASE = 'coffee_shop.sqlite'

def init_db():
    if os.path.exists(DATABASE):
        os.remove(DATABASE)

    conn = sqlite3.connect(DATABASE)
    with open('schema.sql', 'r') as f:
        conn.executescript(f.read())

    cursor = conn.cursor()

    # 1. Seed Roles
    print("Seeding Roles...")
    cursor.execute("INSERT INTO roles (name) VALUES ('admin')")
    cursor.execute("INSERT INTO roles (name) VALUES ('cashier')")

    # 2. Seed Admin User
    print("Seeding Admin User...")
    # Using a simple default password 'admin123'
    password_hash = generate_password_hash('admin123')
    cursor.execute(
        "INSERT INTO users (role_id, username, password_hash, full_name) VALUES (?, ?, ?, ?)",
        (1, 'admin', password_hash, 'System Administrator')
    )

    # 3. Seed Cashier User
    print("Seeding Cashier User...")
    cashier_hash = generate_password_hash('cashier123')
    cursor.execute(
        "INSERT INTO users (role_id, username, password_hash, full_name) VALUES (?, ?, ?, ?)",
        (2, 'cashier', cashier_hash, 'John Cashier')
    )

    # 4. Seed Categories
    print("Seeding Categories...")
    categories = ['Coffee', 'Tea', 'Pastry', 'Beverage']
    for cat in categories:
        cursor.execute("INSERT INTO categories (name) VALUES (?)", (cat,))

    # 5. Seed Products
    print("Seeding Products...")
    # Coffee (Not inventory managed)
    cursor.execute("""
        INSERT INTO products (category_id, name, price, is_inventory_managed, stock_quantity)
        VALUES (1, 'Latte', 4.50, 0, 0)
    """)
    cursor.execute("""
        INSERT INTO products (category_id, name, price, is_inventory_managed, stock_quantity)
        VALUES (1, 'Cappuccino', 4.00, 0, 0)
    """)

    # Beverage (Inventory managed)
    cursor.execute("""
        INSERT INTO products (category_id, name, price, is_inventory_managed, stock_quantity)
        VALUES (4, 'Bottled Water', 1.50, 1, 50)
    """)
    cursor.execute("""
        INSERT INTO products (category_id, name, price, is_inventory_managed, stock_quantity)
        VALUES (4, 'Orange Juice', 3.00, 1, 20)
    """)

    conn.commit()
    conn.close()
    print("Database initialization complete.")

if __name__ == '__main__':
    init_db()
