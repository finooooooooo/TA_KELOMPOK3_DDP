import functools
from flask import g, redirect, url_for, session, abort

def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('auth.login'))
        return view(**kwargs)
    return wrapped_view

def admin_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('auth.login'))

        # Check if role is admin (role_id 1 based on seed, but better check name)
        # We stored role_name in session during login
        if session.get('role_name') != 'admin':
            abort(403) # Forbidden

        return view(**kwargs)
    return wrapped_view

def cashier_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('auth.login'))

        # Both admin and cashier can likely access POS?
        # Spec says: "Admin: Full access... Cashier: RESTRICTED access. Can ONLY access the POS Transaction Page."
        # Does Admin have access to POS? usually yes.
        # But let's assume if the route is strictly for POS, check if user is allowed.
        # We'll allow both for POS for now, or just check login.

        return view(**kwargs)
    return wrapped_view
