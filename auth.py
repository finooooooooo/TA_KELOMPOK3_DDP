from flask import Blueprint, render_template, request, redirect, url_for, flash, session, g
from werkzeug.security import check_password_hash
import db
import functools

bp = Blueprint('auth', __name__, url_prefix='/auth')

@bp.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        database = db.get_db()
        error = None

        user = database.execute(
            'SELECT * FROM users WHERE username = ?', (username,)
        ).fetchone()

        if user is None:
            error = 'Incorrect username.'
        elif not check_password_hash(user['password_hash'], password):
            error = 'Incorrect password.'

        if error is None:
            session.clear()
            session['user_id'] = user['id']
            session['role_id'] = user['role_id']

            # Get role name
            role = database.execute(
                'SELECT name FROM roles WHERE id = ?', (user['role_id'],)
            ).fetchone()
            session['role_name'] = role['name']

            if role['name'] == 'admin':
                return redirect(url_for('admin.dashboard'))
            elif role['name'] == 'cashier':
                return redirect(url_for('pos.index'))
            else:
                return redirect(url_for('index'))

        flash(error)

    return render_template('auth/login.html')

@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login'))

@bp.before_app_request
def load_logged_in_user():
    user_id = session.get('user_id')

    if user_id is None:
        g.user = None
    else:
        g.user = db.get_db().execute(
            'SELECT * FROM users WHERE id = ?', (user_id,)
        ).fetchone()
