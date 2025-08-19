# auth_middleware.py
# auth_middleware.py
from functools import wraps
from flask import session, redirect, url_for, flash, request, jsonify

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'error': 'Sesión expirada', 'redirect': url_for('views.login_page')}), 401
            flash('Por favor inicie sesión para acceder a esta página.', 'warning')
            return redirect(url_for('views.login_page'))
        return f(*args, **kwargs)
    return decorated_function

def role_required(role_id):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if session.get('id_rol') != role_id:
                flash('No tiene permisos para acceder a esta página.', 'danger')
                return redirect(url_for('views.dashboard'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator