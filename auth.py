from flask import Blueprint, render_template, request, redirect, url_for, flash, session, g
from werkzeug.security import check_password_hash
import db
import functools

# Inisialisasi Blueprint
bp = Blueprint('auth', __name__, url_prefix='/auth')

@bp.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        database = db.get_db()
        error = None

        # Cek User di Database (Pakai Cursor Aman)
        with database.cursor() as cur:
            cur.execute('SELECT * FROM users WHERE username = %s', (username,))
            user = cur.fetchone()

            if user is None:
                error = 'Username tidak ditemukan.'
            elif not check_password_hash(user['password_hash'], password):
                error = 'Password salah.'

            if error is None:
                # Login Berhasil -> Simpan Sesi
                session.clear()
                session['user_id'] = user['id']
                session['role_id'] = user['role_id']

                # Ambil Nama Role (Admin/Cashier)
                cur.execute('SELECT name FROM roles WHERE id = %s', (user['role_id'],))
                role = cur.fetchone()
                
                if role:
                    session['role_name'] = role['name']
                    
                    # Redirect sesuai Role
                    if role['name'] == 'admin':
                        return redirect(url_for('admin.dashboard'))
                    elif role['name'] == 'cashier':
                        return redirect(url_for('pos.index'))
                
                # Default fallback
                return redirect(url_for('pos.index'))

        # Kalau ada error, tampilkan
        flash(error, 'error')

    return render_template('auth/login.html')

@bp.route('/logout')
def logout():
    """Membersihkan sesi dan redirect ke halaman login."""
    session.clear()
    # PASTIKAN REDIRECT KE AUTH.LOGIN, BUKAN KE ROUTE YANG GAK ADA
    return redirect(url_for('auth.login'))

@bp.before_app_request
def load_logged_in_user():
    """Cek apakah user sedang login di setiap request."""
    user_id = session.get('user_id')

    if user_id is None:
        g.user = None
    else:
        database = db.get_db()
        # Gunakan cursor context manager agar tidak error di Postgres
        with database.cursor() as cur:
            cur.execute('SELECT * FROM users WHERE id = %s', (user_id,))
            g.user = cur.fetchone()