let products = [];
let categories = [];
let cart = {}; // Object: productId -> { product, quantity }

// Formatter for IDR (Rupiah, No Decimals)
const formatter = new Intl.NumberFormat('id-ID', {
    style: 'currency',
    currency: 'IDR',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0
});

document.addEventListener('DOMContentLoaded', () => {
    fetchProducts();
    setupEventListeners();
});

function setupEventListeners() {
    // QRIS Logic Toggle
    const paymentSelect = document.getElementById('payment-method');
    
    if (paymentSelect) {
        paymentSelect.addEventListener('change', (e) => {
            const method = e.target.value;
            const cashArea = document.getElementById('cash-payment-area');
            const qrisArea = document.getElementById('qris-payment-area');
            const amountInput = document.getElementById('amount-received');
            const confirmBtn = document.getElementById('confirm-pay-btn');
            
            if (method === 'qris') {
                // TAMPILAN: Sembunyikan Cash, Munculkan QRIS
                cashArea.classList.add('hidden');
                qrisArea.classList.remove('hidden');
                
                // LOGIKA: Auto-fill harga pas (Termasuk Pajak)
                const subtotal = Object.values(cart).reduce((sum, item) => sum + (item.product.price * item.quantity), 0);
                const tax = Math.round(subtotal * 0.10);
                const total = subtotal + tax;
                
                amountInput.value = total; // Isi otomatis input tersembunyi
                
                // Matikan validasi visual, langsung enable tombol
                document.getElementById('validation-msg').classList.add('hidden');
                confirmBtn.disabled = false;
                confirmBtn.innerText = "Verify & Finish Payment"; 
                confirmBtn.classList.remove('bg-blue-600', 'hover:bg-blue-700');
                confirmBtn.classList.add('bg-green-600', 'hover:bg-green-700');
                
            } else {
                // TAMPILAN: Balik ke Cash
                cashArea.classList.remove('hidden');
                qrisArea.classList.add('hidden');
                
                // Reset input
                amountInput.value = '';
                document.getElementById('change-display').innerText = formatter.format(0);
                confirmBtn.disabled = true;
                confirmBtn.innerText = "Confirm Payment";
                confirmBtn.classList.add('bg-blue-600', 'hover:bg-blue-700');
                confirmBtn.classList.remove('bg-green-600', 'hover:bg-green-700');
            }
        });
    }
}

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
    let html = `<button onclick="renderProducts('all')" class="px-4 py-2 bg-gray-200 rounded-full hover:bg-gray-300 focus:bg-blue-900 focus:text-white whitespace-nowrap transition">All</button>`;

    categories.forEach(cat => {
        html += `<button onclick="renderProducts(${cat.id})" class="px-4 py-2 bg-gray-200 rounded-full hover:bg-gray-300 focus:bg-blue-900 focus:text-white whitespace-nowrap transition">${cat.name}</button>`;
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
        const isOutOfStock = p.is_inventory_managed && p.stock_quantity <= 0;
        
        // Cek kuantitas di cart buat badge
        const inCart = cart[p.id] ? cart[p.id].quantity : 0;

        const card = document.createElement('div');
        card.className = `bg-white p-4 rounded-xl shadow-sm border border-gray-100 cursor-pointer transition transform hover:scale-105 relative ${isOutOfStock ? 'opacity-60 cursor-not-allowed' : ''}`;
        
        if (!isOutOfStock) {
            card.onclick = () => addToCart(p.id);
        }

        card.innerHTML = `
            ${inCart > 0 ? `<div class="absolute top-2 right-2 bg-blue-600 text-white text-xs font-bold w-6 h-6 flex items-center justify-center rounded-full shadow-md z-10">${inCart}</div>` : ''}
            
            <div class="h-32 bg-gray-100 rounded-lg mb-3 flex items-center justify-center overflow-hidden">
                ${p.image_url ?
                    `<img src="/static/${p.image_url}" class="h-full w-full object-cover" onerror="this.onerror=null;this.parentElement.innerText='No Image';">`
                    : '<span class="text-gray-400 text-sm">No Image</span>'}
            </div>
            <h3 class="font-bold text-gray-800 text-sm h-10 leading-tight overflow-hidden">${p.name}</h3>
            <div class="flex justify-between items-center mt-2">
                <span class="font-bold text-blue-700">${formatter.format(p.price)}</span>
                ${isOutOfStock ? `<span class="text-xs text-red-500 font-bold">Habis</span>` : 
                  (p.is_inventory_managed ? `<span class="text-xs text-gray-500">Stok: ${p.stock_quantity}</span>` : '')}
            </div>
        `;

        container.appendChild(card);
    });
}

// Toast Notification (Pengganti Alert)
function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container') || createToastContainer();
    
    const toast = document.createElement('div');
    const bgClass = type === 'error' ? 'bg-red-500' : (type === 'success' ? 'bg-green-500' : 'bg-blue-600');

    toast.className = `${bgClass} text-white px-6 py-3 rounded-lg shadow-xl mb-3 transform transition-all duration-500 translate-x-full flex items-center min-w-[300px]`;
    toast.innerHTML = `
        <span class="font-bold mr-2 text-lg">${type === 'error' ? '!' : '✓'}</span>
        <span class="font-medium">${message}</span>
    `;

    container.appendChild(toast);

    // Slide In
    requestAnimationFrame(() => {
        toast.classList.remove('translate-x-full');
    });

    // Remove after 3s
    setTimeout(() => {
        toast.classList.add('translate-x-full', 'opacity-0');
        setTimeout(() => toast.remove(), 500);
    }, 3000);
}

function createToastContainer() {
    const div = document.createElement('div');
    div.id = 'toast-container';
    div.className = 'fixed top-5 right-5 z-[9999] flex flex-col items-end';
    document.body.appendChild(div);
    return div;
}

function addToCart(productId) {
    const product = products.find(p => p.id === productId);

    if (product.is_inventory_managed) {
        const currentQty = cart[productId] ? cart[productId].quantity : 0;
        if (currentQty >= product.stock_quantity) {
            showToast(`Stok habis! Sisa hanya ${product.stock_quantity}`, 'error');
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
    renderProducts('all'); // Refresh badges
}

function updateQuantity(productId, change) {
    if (cart[productId]) {
        const newQty = cart[productId].quantity + change;

        if (newQty <= 0) {
            delete cart[productId];
        } else {
            if (change > 0 && cart[productId].product.is_inventory_managed) {
                if (newQty > cart[productId].product.stock_quantity) {
                    showToast(`Stok tidak cukup!`, 'error');
                    return;
                }
            }
            cart[productId].quantity = newQty;
        }
        renderCart();
        renderProducts('all'); // Refresh badges
    }
}

function renderCart() {
    const container = document.getElementById('cart-items');
    const totalEl = document.getElementById('cart-total');
    const checkoutBtn = document.getElementById('checkout-btn');

    container.innerHTML = '';
    let subtotal = 0;

    const itemIds = Object.keys(cart);

    if (itemIds.length === 0) {
        container.innerHTML = '<div class="text-center text-gray-400 mt-10 italic">Keranjang kosong</div>';
        checkoutBtn.disabled = true;
        totalEl.innerText = formatter.format(0);
        return;
    }

    checkoutBtn.disabled = false;

    itemIds.forEach(id => {
        const item = cart[id];
        const itemSubtotal = item.product.price * item.quantity;
        subtotal += itemSubtotal;

        const div = document.createElement('div');
        div.className = 'flex justify-between items-center bg-gray-50 p-3 rounded-lg border border-gray-100';
        div.innerHTML = `
            <div class="flex-1">
                <div class="font-bold text-gray-800">${item.product.name}</div>
                <div class="text-xs text-gray-500">${formatter.format(item.product.price)} x ${item.quantity}</div>
            </div>
            <div class="font-bold text-gray-700 mr-3">${formatter.format(itemSubtotal)}</div>
            <div class="flex space-x-1">
                <button onclick="updateQuantity(${id}, -1)" class="w-7 h-7 bg-red-100 text-red-600 rounded hover:bg-red-200 font-bold">-</button>
                <button onclick="updateQuantity(${id}, 1)" class="w-7 h-7 bg-blue-100 text-blue-600 rounded hover:bg-blue-200 font-bold">+</button>
            </div>
        `;
        container.appendChild(div);
    });

    const tax = Math.round(subtotal * 0.10);
    const total = subtotal + tax;

    // Breakdown
    const summaryDiv = document.createElement('div');
    summaryDiv.className = 'mt-4 border-t border-dashed border-gray-300 pt-3 text-sm space-y-1';
    summaryDiv.innerHTML = `
        <div class="flex justify-between text-gray-600"><span>Subtotal:</span> <span>${formatter.format(subtotal)}</span></div>
        <div class="flex justify-between text-gray-500"><span>Pajak (10%):</span> <span>${formatter.format(tax)}</span></div>
    `;
    container.appendChild(summaryDiv);

    totalEl.innerText = formatter.format(total);
}

// Checkout Logic Global
let currentGrandTotal = 0;

function openCheckoutModal() {
    const modal = document.getElementById('checkout-modal');
    modal.classList.remove('hidden');

    const subtotal = Object.values(cart).reduce((sum, item) => sum + (item.product.price * item.quantity), 0);
    const tax = Math.round(subtotal * 0.10);
    currentGrandTotal = subtotal + tax;

    document.getElementById('modal-total-display').innerText = formatter.format(currentGrandTotal);

    // Reset default state (CASH)
    document.getElementById('payment-method').value = 'cash';
    
    // Tampilkan area Cash, sembunyikan QRIS
    document.getElementById('cash-payment-area').classList.remove('hidden');
    document.getElementById('qris-payment-area').classList.add('hidden');

    // Reset inputs
    document.getElementById('amount-received').value = '';
    document.getElementById('change-display').innerText = formatter.format(0);
    document.getElementById('validation-msg').classList.add('hidden');
    
    // Reset Tombol
    const btn = document.getElementById('confirm-pay-btn');
    btn.disabled = true;
    btn.innerText = "Confirm Payment";
    btn.classList.add('bg-blue-600');
    btn.classList.remove('bg-green-600');
}

function closeCheckoutModal() {
    document.getElementById('checkout-modal').classList.add('hidden');
}

function calculateChange() {
    const received = parseFloat(document.getElementById('amount-received').value) || 0;
    const change = received - currentGrandTotal;
    const btn = document.getElementById('confirm-pay-btn');
    const msg = document.getElementById('validation-msg');

    if (change >= 0) {
        document.getElementById('change-display').innerText = formatter.format(change);
        btn.disabled = false;
        msg.classList.add('hidden');
    } else {
        document.getElementById('change-display').innerText = formatter.format(0);
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
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        const result = await response.json();

        if (response.ok) {
            showToast(`Transaksi Sukses! Kode: ${result.transaction_code}`, 'success');
            cart = {};
            renderCart();
            closeCheckoutModal();
            fetchProducts(); // Refresh stock
        } else {
            showToast(`Gagal: ${result.error}`, 'error');
        }
    } catch (error) {
        console.error('Order error:', error);
        showToast('Terjadi kesalahan koneksi.', 'error');
    }
}