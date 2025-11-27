from flask import Blueprint, render_template, request, g, redirect, url_for, flash, session
from decorators import login_required, admin_required
import db
import services

bp = Blueprint('admin', __name__, url_prefix='/admin')

@bp.route('/dashboard')
@admin_required
def dashboard():
    database = db.get_db()

    # Reports: Fetch all transactions
    # Default to last 30 days or something? For now, fetch all.
    query = """
        SELECT o.id, o.transaction_code, o.total_amount, o.status, o.created_at, u.username as cashier_name
        FROM orders o
        JOIN users u ON o.user_id = u.id
        ORDER BY o.created_at DESC
    """
    orders = database.execute(query).fetchall()

    return render_template('admin/dashboard.html', orders=orders)

@bp.route('/products')
@admin_required
def products():
    database = db.get_db()
    products = database.execute("""
        SELECT p.*, c.name as category_name
        FROM products p
        JOIN categories c ON p.category_id = c.id
        ORDER BY p.name
    """).fetchall()
    categories = database.execute("SELECT * FROM categories").fetchall()
    return render_template('admin/products.html', products=products, categories=categories)

@bp.route('/products/add', methods=['POST'])
@admin_required
def add_product():
    name = request.form['name']
    category_id = request.form['category_id']
    price = request.form['price']
    is_inventory_managed = 'is_inventory_managed' in request.form
    stock_quantity = request.form.get('stock_quantity', 0)

    database = db.get_db()
    database.execute(
        "INSERT INTO products (name, category_id, price, is_inventory_managed, stock_quantity) VALUES (?, ?, ?, ?, ?)",
        (name, category_id, price, is_inventory_managed, stock_quantity)
    )
    database.commit()
    return redirect(url_for('admin.products'))

@bp.route('/products/edit/<int:id>', methods=['POST'])
@admin_required
def edit_product(id):
    name = request.form['name']
    category_id = request.form['category_id']
    price = request.form['price']
    is_inventory_managed = 'is_inventory_managed' in request.form
    stock_quantity = request.form.get('stock_quantity', 0)
    is_active = 'is_active' in request.form

    database = db.get_db()
    database.execute(
        """UPDATE products
           SET name=?, category_id=?, price=?, is_inventory_managed=?, stock_quantity=?, is_active=?
           WHERE id=?""",
        (name, category_id, price, is_inventory_managed, stock_quantity, is_active, id)
    )
    database.commit()
    return redirect(url_for('admin.products'))

@bp.route('/void/<int:order_id>', methods=['POST'])
@admin_required
def void_transaction(order_id):
    database = db.get_db()
    try:
        services.void_order(database, order_id, session['user_id'])
        flash('Order voided successfully.', 'success')
    except Exception as e:
        flash(f'Error voiding order: {str(e)}', 'error')

    return redirect(url_for('admin.dashboard'))
