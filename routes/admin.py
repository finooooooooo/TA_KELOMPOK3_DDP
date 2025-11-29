from flask import Blueprint, render_template, request, g, redirect, url_for, flash, session, current_app
from decorators import login_required, admin_required
import db
import services
import os
from werkzeug.utils import secure_filename

bp = Blueprint('admin', __name__, url_prefix='/admin')

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@bp.route('/dashboard')
@admin_required
def dashboard():
    database = db.get_db()

    # Reports: Fetch all transactions
    # Menggunakan Cursor Context Manager
    query = """
        SELECT o.id, o.transaction_code, o.total_amount, o.status, o.created_at, u.username as cashier_name
        FROM orders o
        JOIN users u ON o.user_id = u.id
        ORDER BY o.created_at DESC
    """
    
    # PERBAIKAN: Pakai Cursor
    with database.cursor() as cur:
        cur.execute(query)
        orders = cur.fetchall()

    return render_template('admin/dashboard.html', orders=orders)

@bp.route('/products')
@admin_required
def products():
    database = db.get_db()
    
    # PERBAIKAN: Pakai Cursor untuk fetch products & categories
    with database.cursor() as cur:
        # Ambil Produk
        cur.execute("""
            SELECT p.*, c.name as category_name
            FROM products p
            JOIN categories c ON p.category_id = c.id
            ORDER BY p.name
        """)
        products = cur.fetchall()
        
        # Ambil Kategori
        cur.execute("SELECT * FROM categories")
        categories = cur.fetchall()

    return render_template('admin/products.html', products=products, categories=categories)

@bp.route('/products/add', methods=['POST'])
@admin_required
def add_product():
    name = request.form['name']
    category_id = request.form['category_id']
    price = request.form['price']
    is_inventory_managed = 'is_inventory_managed' in request.form
    stock_quantity = request.form.get('stock_quantity', 0)

    image_url = ''
    if 'image' in request.files:
        file = request.files['image']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            upload_folder = current_app.config['UPLOAD_FOLDER']
            
            # Ensure upload folder exists
            os.makedirs(os.path.join(current_app.root_path, upload_folder), exist_ok=True)

            filepath = os.path.join(current_app.root_path, upload_folder, filename)
            file.save(filepath)
            
            # Store relative path for frontend (e.g. 'uploads/foto.jpg')
            # Note: Di app.py config UPLOAD_FOLDER biasanya 'static/uploads'
            # Kita simpan string 'uploads/filename' agar di HTML bisa panggil static
            image_url = f"uploads/{filename}"

    database = db.get_db()
    
    # PERBAIKAN: Pakai Cursor + Commit
    with database.cursor() as cur:
        cur.execute(
            "INSERT INTO products (name, category_id, price, is_inventory_managed, stock_quantity, image_url) VALUES (%s, %s, %s, %s, %s, %s)",
            (name, category_id, price, is_inventory_managed, stock_quantity, image_url)
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

    # Handle Image Upload
    update_image_sql = ""
    params = [name, category_id, price, is_inventory_managed, stock_quantity, is_active]

    if 'image' in request.files:
        file = request.files['image']
        if file and file.filename != '' and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            upload_folder = current_app.config['UPLOAD_FOLDER']
            os.makedirs(os.path.join(current_app.root_path, upload_folder), exist_ok=True)

            filepath = os.path.join(current_app.root_path, upload_folder, filename)
            file.save(filepath)

            image_url = f"uploads/{filename}"
            update_image_sql = ", image_url=%s"
            params.append(image_url)

    params.append(id)

    query = f"""UPDATE products 
            SET name=%s, category_id=%s, price=%s, is_inventory_managed=%s, stock_quantity=%s, is_active=%s {update_image_sql}
            WHERE id=%s"""

    # PERBAIKAN: Pakai Cursor + Commit
    with database.cursor() as cur:
        cur.execute(query, tuple(params))
        database.commit()
        
    return redirect(url_for('admin.products'))

@bp.route('/void/<int:order_id>', methods=['POST'])
@admin_required
def void_transaction(order_id):
    database = db.get_db()
    try:
        # services.void_order sudah kita minta refactor sebelumnya untuk handle cursor internal
        # atau menerima koneksi dan membuat cursor sendiri.
        services.void_order(database, order_id, session['user_id'])
        flash('Order voided successfully.', 'success')
    except Exception as e:
        flash(f'Error voiding order: {str(e)}', 'error')

    return redirect(url_for('admin.dashboard'))