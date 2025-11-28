# CoffeePOS Technical Documentation & Code Walkthrough

## 1. Project Overview & Tech Stack

This project is an **Enterprise-Standard Point of Sale (POS) System** designed for reliability, financial accuracy, and security.

### Why this Tech Stack?

*   **Backend: Python Flask**
    *   **Why Flask?** We chose Flask over Django because of its **micro-framework architecture**. It gives us granular control over the database connections and transaction management (`try... except... rollback`) without the "black box" magic of Django's ORM. This is crucial for a financial application where we need to know exactly when a transaction commits.

*   **Database: PostgreSQL**
    *   **Why PostgreSQL?** SQLite is not suitable for concurrent write operations (locking issues). PostgreSQL handles high-concurrency writes efficiently (MVCC).
    *   **Reliability:** It supports robust transaction ACID properties and strict data types (`DECIMAL` for money).

*   **Frontend: Jinja2 + Tailwind CSS + Vanilla JS**
    *   **Why no React/Vue?** Simplicity and Speed. The "Server-Side Rendering" (SSR) approach reduces the complexity of maintaining a separate API state and frontend state. Vanilla JS is used only for lightweight DOM manipulation (Cart logic), ensuring the app loads instantly on low-end hardware often found in coffee shops.

*   **Desktop Wrapper: `pywebview`**
    *   **How it works:** Instead of building a separate Electron app (which is heavy), `pywebview` launches a lightweight web view window that renders our Flask application locally. It provides a native desktop experience with a fraction of the resource usage.

---

## 2. Database Schema (The Backbone)

Our schema corresponds to the Entity-Relationship logic required for a retail business.

### Crucial Columns & Explanations

1.  **`products.is_inventory_managed` (Hybrid Inventory)**
    *   **Purpose:** Differentiates between items that need stock tracking and those that don't.
    *   **Logic:**
        *   `TRUE` (e.g., Bottled Water): System STRICTLY prevents sale if `stock_quantity` < requested quantity. Deducts stock on sale.
        *   `FALSE` (e.g., Latte): System allows infinite sales. Used for made-to-order items where we track raw ingredients separately (or not at all in this scope).

2.  **`order_items.product_name_snapshot` & `price_snapshot`**
    *   **Why Snapshot?** This is an **Audit Trail** requirement.
    *   **Scenario:** A customer buys a coffee for $5. Tomorrow, we change the price to $6.
    *   **Mistake:** If we just linked to `products.id`, historical reports would show the old order was $6.
    *   **Solution:** We copy the *current* price and name into the `order_items` table at the moment of purchase.

3.  **`orders.tax_amount`**
    *   **Financial Logic:** We calculate a 10% tax on the subtotal.
    *   **Storage:** We store the explicit tax amount separate from `total_amount` to facilitate tax reporting to authorities without re-calculating (and potentially hitting rounding errors) later.

4.  **`users.role_id`**
    *   **RBAC (Role-Based Access Control):** Links to the `roles` table. Allows us to restrict sensitive actions (like Voiding an order or adding Inventory) to `admin` users only.

---

## 3. Backend Code Walkthrough

### `app.py` & `run_gui.py`
*   **`create_app()`**: The Factory Pattern function. It initializes the Flask app, registers Blueprints (routes), and configures the Database connection.
*   **`webview.create_window`**: In `run_gui.py`, this function spins up a native OS window (Cocoa on Mac, GTK on Linux, WinForms on Windows) and points it to our local Flask server (`localhost:5000`).

### `db.py`
*   **`psycopg2`**: The PostgreSQL adapter for Python.
*   **`get_db()`**: Handles the connection lifecycle. We use `g` (Flask global) to ensure one connection per request.
*   **`RealDictCursor`**: Crucial! It makes the database return rows as Python Dictionaries (`row['id']`) instead of Tuples (`row[0]`). This makes the code readable (`row['price']` vs `row[3]`).

### `auth.py`
*   **`werkzeug.security`**:
    *   `generate_password_hash`: Hashes passwords (PBKDF2/SHA256) before storing them. **We never store plain text passwords.**
    *   `check_password_hash`: Verifies a login attempt against the hash.
*   **`session`**: A signed cookie that stores the `user_id`. If tampered with, the signature becomes invalid, logging the user out.
*   **`@login_required`**: A Decorator. It wraps a view function. If `g.user` is None, it aborts the request and redirects to login. `functools.wraps` is used to preserve the metadata (name, docstring) of the original function.

### `services.py` (THE BRAIN)
This file handles **Business Logic** decoupled from the HTTP layer.

*   **`process_order(...)`**:
    *   **Atomic Transaction:** The entire function is wrapped in `try... except... rollback`. This ensures that if *anything* fails (e.g., stock deduction succeeds but payment recording fails), the database reverts to the state *before* the transaction started. Zero data corruption.
    *   **Stock Logic:** It queries `products`. If `is_inventory_managed` is True, it asserts `stock >= qty`. If valid, it runs `UPDATE products SET stock = stock - qty`.
    *   **Tax Math:**
        ```python
        tax_amount = total_amount * Decimal('0.10')
        grand_total = total_amount + tax_amount
        ```
        We use `Decimal` for all money math to avoid floating-point errors (e.g., `0.1 + 0.2 != 0.3` in floats).

---

## 4. Frontend Logic (`static/js/pos.js`)

*   **State Management (`let cart = {}`)**:
    *   We use a simple JavaScript Object to track the cart client-side. Key = Product ID, Value = {Product Object, Quantity}.

*   **`renderProducts()`**:
    *   Dynamically builds HTML cards. It checks `stock_quantity` to visually disable items that are out of stock.
    *   **Currency Formatting:** We use `Intl.NumberFormat('id-ID', ...)` to display "Rp" correctly formatted.

*   **`renderCart()`**:
    *   Re-draws the cart list every time an item is added.
    *   **Calculates Totals:** It sums up the subtotal, calculates 10% tax, and displays the Grand Total *before* the user clicks checkout.

*   **QRIS Logic (Auto-fill)**:
    *   Event Listener on the payment method dropdown.
    *   If "QRIS" is selected, the script automatically fills the "Amount Received" input with the exact `Grand Total`. This creates a smoother UX for digital payments where exact change is guaranteed.

---

## 5. Common "Viva/Defense" Questions

**Q: "What happens if the internet cuts off during a transaction?"**
**A:** Since this is a Local-First deployment (Localhost Database + Desktop Wrapper), it works offline. However, regarding data integrity: We use **Atomic Transactions**. If the power fails halfway through writing to the database, PostgreSQL's Write-Ahead Log (WAL) ensures that upon restart, the incomplete transaction is rolled back. The database is never left in an inconsistent state.

**Q: "How do you handle decimal rounding errors?"**
**A:** We strictly use the `DECIMAL` data type in PostgreSQL and the `decimal.Decimal` class in Python. We **never** use `float` for currency. `Float` uses binary approximation (IEEE 754), which causes errors like `1.00 - 0.90 = 0.09999999`. `Decimal` uses fixed-point arithmetic, which is exact.

**Q: "Is the data secure?"**
**A:** Yes.
1.  **Passwords:** Hashed using PBKDF2 (Industry standard).
2.  **Access:** Routes are protected by `@login_required`.
3.  **Roles:** Critical actions are protected by Role checks (RBAC).
4.  **Audit:** We snapshot prices in `order_items` so tampering with the master product list doesn't alter historical financial records.
