let products = [];
let categories = [];
let cart = {}; // Object: productId -> { product, quantity }

document.addEventListener('DOMContentLoaded', () => {
    fetchProducts();
});

async function fetchProducts() {
    try {
        const response = await fetch('/api/products');
        const data = await response.json();
        products = data.products;
        categories = data.categories;

        renderCategories();
        renderProducts('all');
    } catch (error) {
        console.error('Error fetching products:', error);
    }
}

function renderCategories() {
    const container = document.getElementById('category-filter');
    let html = `<button onclick="renderProducts('all')" class="px-4 py-2 bg-gray-200 rounded-full hover:bg-gray-300 focus:bg-blue-500 focus:text-white whitespace-nowrap">All</button>`;

    categories.forEach(cat => {
        html += `<button onclick="renderProducts(${cat.id})" class="px-4 py-2 bg-gray-200 rounded-full hover:bg-gray-300 focus:bg-blue-500 focus:text-white whitespace-nowrap">${cat.name}</button>`;
    });

    container.innerHTML = html;
}

function renderProducts(categoryId) {
    const container = document.getElementById('product-grid');
    container.innerHTML = '';

    const filtered = categoryId === 'all'
        ? products
        : products.filter(p => p.category_id === categoryId);

    filtered.forEach(p => {
        // Logic: If managed and stock 0, disable
        const isOutOfStock = p.is_inventory_managed && p.stock_quantity <= 0;

        const card = document.createElement('div');
        card.className = `bg-white p-4 rounded-lg shadow cursor-pointer transition transform hover:scale-105 ${isOutOfStock ? 'opacity-50 cursor-not-allowed' : ''}`;
        if (!isOutOfStock) {
            card.onclick = () => addToCart(p.id);
        }

        card.innerHTML = `
            <div class="h-24 bg-gray-200 rounded mb-2 flex items-center justify-center text-gray-400">
                ${p.image_url ? `<img src="${p.image_url}" class="h-full w-full object-cover rounded">` : 'No Image'}
            </div>
            <h3 class="font-bold text-gray-800 text-sm h-10 overflow-hidden">${p.name}</h3>
            <div class="flex justify-between items-center mt-2">
                <span class="font-bold text-blue-600">$${p.price.toFixed(2)}</span>
                ${p.is_inventory_managed ? `<span class="text-xs text-gray-500">Stock: ${p.stock_quantity}</span>` : ''}
            </div>
        `;

        container.appendChild(card);
    });
}

function addToCart(productId) {
    const product = products.find(p => p.id === productId);

    // Check local stock limit if managed
    if (product.is_inventory_managed) {
        const currentQty = cart[productId] ? cart[productId].quantity : 0;
        if (currentQty >= product.stock_quantity) {
            alert('Insufficient stock!');
            return;
        }
    }

    if (cart[productId]) {
        cart[productId].quantity++;
    } else {
        cart[productId] = {
            product: product,
            quantity: 1
        };
    }
    renderCart();
}

function updateQuantity(productId, change) {
    if (cart[productId]) {
        const newQty = cart[productId].quantity + change;

        if (newQty <= 0) {
            delete cart[productId];
        } else {
            // Check stock limit on increase
            if (change > 0 && cart[productId].product.is_inventory_managed) {
                if (newQty > cart[productId].product.stock_quantity) {
                    alert('Insufficient stock!');
                    return;
                }
            }
            cart[productId].quantity = newQty;
        }
        renderCart();
    }
}

function renderCart() {
    const container = document.getElementById('cart-items');
    const totalEl = document.getElementById('cart-total');
    const checkoutBtn = document.getElementById('checkout-btn');

    container.innerHTML = '';
    let total = 0;

    const itemIds = Object.keys(cart);

    if (itemIds.length === 0) {
        container.innerHTML = '<div class="text-center text-gray-500 mt-10">Cart is empty</div>';
        checkoutBtn.disabled = true;
        totalEl.innerText = '$0.00';
        return;
    }

    checkoutBtn.disabled = false;

    itemIds.forEach(id => {
        const item = cart[id];
        const subtotal = item.product.price * item.quantity;
        total += subtotal;

        const div = document.createElement('div');
        div.className = 'flex justify-between items-center bg-gray-100 p-2 rounded';
        div.innerHTML = `
            <div class="flex-1">
                <div class="font-bold text-sm">${item.product.name}</div>
                <div class="text-xs text-gray-500">$${item.product.price.toFixed(2)} x ${item.quantity}</div>
            </div>
            <div class="font-bold text-gray-700 mr-4">$${subtotal.toFixed(2)}</div>
            <div class="flex space-x-1">
                <button onclick="updateQuantity(${id}, -1)" class="w-6 h-6 bg-red-200 text-red-700 rounded flex items-center justify-center hover:bg-red-300">-</button>
                <button onclick="updateQuantity(${id}, 1)" class="w-6 h-6 bg-green-200 text-green-700 rounded flex items-center justify-center hover:bg-green-300">+</button>
            </div>
        `;
        container.appendChild(div);
    });

    totalEl.innerText = '$' + total.toFixed(2);
}

// Checkout Logic
let currentTotal = 0;

function openCheckoutModal() {
    const modal = document.getElementById('checkout-modal');
    modal.classList.remove('hidden');

    currentTotal = Object.values(cart).reduce((sum, item) => sum + (item.product.price * item.quantity), 0);
    document.getElementById('modal-total-display').innerText = '$' + currentTotal.toFixed(2);

    // Reset inputs
    document.getElementById('amount-received').value = '';
    document.getElementById('change-display').innerText = '$0.00';
    document.getElementById('validation-msg').classList.add('hidden');
    document.getElementById('confirm-pay-btn').disabled = true;
}

function closeCheckoutModal() {
    document.getElementById('checkout-modal').classList.add('hidden');
}

function calculateChange() {
    const received = parseFloat(document.getElementById('amount-received').value) || 0;
    const change = received - currentTotal;
    const btn = document.getElementById('confirm-pay-btn');
    const msg = document.getElementById('validation-msg');

    if (change >= 0) {
        document.getElementById('change-display').innerText = '$' + change.toFixed(2);
        btn.disabled = false;
        msg.classList.add('hidden');
    } else {
        document.getElementById('change-display').innerText = '$0.00';
        btn.disabled = true;
        msg.classList.remove('hidden');
    }
}

async function submitOrder() {
    const paymentMethod = document.getElementById('payment-method').value;
    const amountReceived = parseFloat(document.getElementById('amount-received').value);

    const payload = {
        cart: Object.keys(cart).map(id => ({
            product_id: parseInt(id),
            quantity: cart[id].quantity
        })),
        payment_method: paymentMethod,
        amount_received: amountReceived
    };

    try {
        const response = await fetch('/api/orders', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        });

        const result = await response.json();

        if (response.ok) {
            alert(`Order Successful! TRX: ${result.transaction_code}`);
            cart = {};
            renderCart();
            closeCheckoutModal();
            fetchProducts(); // Refresh stock
        } else {
            alert(`Error: ${result.error}`);
        }
    } catch (error) {
        console.error('Order error:', error);
        alert('Failed to submit order.');
    }
}
