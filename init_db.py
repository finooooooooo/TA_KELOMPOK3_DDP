import psycopg2
from werkzeug.security import generate_password_hash

# Kredensial Hardcoded sesuai instruksi
DB_Config = {
    'dbname': 'kasir_db',
    'user': 'postgres',
    'password': '5432',
    'host': 'localhost',
    'port': '5432'
}

def init_db():
    conn = psycopg2.connect(**DB_Config)
    conn.autocommit = True # Penting buat create table
    
    # Baca schema.sql
    with open('schema.sql', 'r') as f:
        sql_commands = f.read()

    with conn.cursor() as cursor:
        print("Executing Schema...")
        cursor.execute(sql_commands)
        
        # 1. Seed Roles
        print("Seeding Roles...")
        cursor.execute("INSERT INTO roles (name) VALUES ('admin')")
        cursor.execute("INSERT INTO roles (name) VALUES ('cashier')")

        # 2. Seed Admin User
        print("Seeding Admin User...")
        password_hash = generate_password_hash('admin123')
        cursor.execute(
            "INSERT INTO users (role_id, username, password_hash, full_name) VALUES (%s, %s, %s, %s)",
            (1, 'admin', password_hash, 'System Administrator')
        )

        # 3. Seed Cashier User
        print("Seeding Cashier User...")
        cashier_hash = generate_password_hash('cashier123')
        cursor.execute(
            "INSERT INTO users (role_id, username, password_hash, full_name) VALUES (%s, %s, %s, %s)",
            (2, 'cashier', cashier_hash, 'John Cashier')
        )

        # 4. Seed Categories
        print("Seeding Categories...")
        categories = ['Coffee', 'Tea', 'Pastry', 'Beverage']
        for cat in categories:
            cursor.execute("INSERT INTO categories (name) VALUES (%s)", (cat,))

        # 5. Seed Products (Pakai harga Integer biar bagus di UI)
        print("Seeding Products...")
        # Coffee (Unlimited)
        cursor.execute("""
            INSERT INTO products (category_id, name, price, is_inventory_managed, stock_quantity) 
            VALUES (1, 'Latte', 25000, FALSE, 0)
        """)
        cursor.execute("""
            INSERT INTO products (category_id, name, price, is_inventory_managed, stock_quantity) 
            VALUES (1, 'Cappuccino', 28000, FALSE, 0)
        """)

        # Beverage (Managed)
        cursor.execute("""
            INSERT INTO products (category_id, name, price, is_inventory_managed, stock_quantity) 
            VALUES (4, 'Bottled Water', 5000, TRUE, 50)
        """)
        cursor.execute("""
            INSERT INTO products (category_id, name, price, is_inventory_managed, stock_quantity) 
            VALUES (4, 'Orange Juice', 15000, TRUE, 20)
        """)

    conn.close()
    print("Database initialization complete (PostgreSQL).")

if __name__ == '__main__':
    init_db()