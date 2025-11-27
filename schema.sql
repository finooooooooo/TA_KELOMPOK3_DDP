-- 1. AUTH & ROLES
CREATE TABLE roles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(50) NOT NULL UNIQUE -- 'admin', 'cashier'
);

CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    role_id INTEGER NOT NULL,
    username VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (role_id) REFERENCES roles(id)
);

-- 2. PRODUCTS (HYBRID INVENTORY)
CREATE TABLE categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(50) NOT NULL UNIQUE
);

CREATE TABLE products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category_id INTEGER NOT NULL,
    name VARCHAR(100) NOT NULL,
    price DECIMAL(15, 2) NOT NULL,
    image_url VARCHAR(255),

    -- LOGIC:
    -- If is_inventory_managed = TRUE (e.g., Bottled Water), system strictly deducts stock_quantity.
    -- If is_inventory_managed = FALSE (e.g., Latte/Kitchen items), system ignores stock_quantity.
    -- is_active is a manual override to hide items from POS.
    is_inventory_managed BOOLEAN DEFAULT FALSE,
    stock_quantity INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,

    FOREIGN KEY (category_id) REFERENCES categories(id)
);

-- 3. ORDERS (HEADER)
CREATE TABLE orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL, -- Cashier
    transaction_code VARCHAR(20) NOT NULL UNIQUE, -- Generate: TRX-YYYYMMDD-XXXX
    total_amount DECIMAL(15, 2) NOT NULL,
    payment_method VARCHAR(50) NOT NULL, -- 'cash', 'qris'
    amount_received DECIMAL(15, 2),
    change_amount DECIMAL(15, 2),
    status VARCHAR(20) DEFAULT 'paid', -- 'paid', 'cancelled'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Void Logic
    voided_by INTEGER,
    voided_at TIMESTAMP,

    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (voided_by) REFERENCES users(id)
);

-- 4. ORDER ITEMS (SNAPSHOTS)
CREATE TABLE order_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,

    -- CRITICAL AUDIT REQUIREMENT:
    -- Store the name and price AT THE MOMENT of purchase.
    -- Do not rely on joining the product table for historical reports.
    product_name_snapshot VARCHAR(100) NOT NULL,
    price_snapshot DECIMAL(15, 2) NOT NULL,

    quantity INTEGER NOT NULL,
    subtotal DECIMAL(15, 2) NOT NULL,
    FOREIGN KEY (order_id) REFERENCES orders(id),
    FOREIGN KEY (product_id) REFERENCES products(id)
);
