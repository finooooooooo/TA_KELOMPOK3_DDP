from flask import Blueprint, jsonify, request, g, session
from decorators import login_required
import db
import services
import datetime
import uuid

bp = Blueprint('api', __name__, url_prefix='/api')

@bp.route('/products', methods=['GET'])
@login_required
def get_products():
    database = db.get_db()
    # Fetch categories for grouping
    categories = database.execute("SELECT id, name FROM categories").fetchall()

    # Fetch active products
    products = database.execute("""
        SELECT p.id, p.category_id, p.name, p.price, p.is_inventory_managed, p.stock_quantity, p.image_url, c.name as category_name
        FROM products p
        JOIN categories c ON p.category_id = c.id
        WHERE p.is_active = 1
    """).fetchall()

    products_list = []
    for p in products:
        products_list.append({
            'id': p['id'],
            'category_id': p['category_id'],
            'category_name': p['category_name'],
            'name': p['name'],
            'price': float(p['price']),
            'is_inventory_managed': bool(p['is_inventory_managed']),
            'stock_quantity': p['stock_quantity'],
            'image_url': p['image_url']
        })

    return jsonify({
        'products': products_list,
        'categories': [{'id': c['id'], 'name': c['name']} for c in categories]
    })

@bp.route('/orders', methods=['POST'])
@login_required
def create_order():
    data = request.get_json()

    if not data:
        return jsonify({'error': 'No data provided'}), 400

    cart_items = data.get('cart', [])
    payment_method = data.get('payment_method')
    amount_received = data.get('amount_received')

    if not cart_items:
        return jsonify({'error': 'Cart is empty'}), 400

    if not payment_method or not amount_received:
        return jsonify({'error': 'Payment details missing'}), 400

    # Generate Transaction Code
    today_str = datetime.datetime.now().strftime('%Y%m%d')
    random_suffix = str(uuid.uuid4().hex)[:4].upper()
    transaction_code = f"TRX-{today_str}-{random_suffix}"

    database = db.get_db()

    try:
        order_id = services.process_order(
            database,
            session['user_id'],
            transaction_code,
            payment_method,
            amount_received,
            cart_items
        )
        return jsonify({'success': True, 'order_id': order_id, 'transaction_code': transaction_code}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400
