from flask import Blueprint, render_template

views_bp = Blueprint('views', __name__)

@views_bp.route('/')
def index():
    return render_template('index.html')

@views_bp.route('/login')
def login_page():
    return render_template('login.html')

@views_bp.route('/forgot_contraseña')
def forgot_contraseña():
    return render_template('forgot_contraseña.html')

@views_bp.route('/reset_contraseña')
def reset_contraseña():
    return render_template('reset_contraseña.html')

@views_bp.route('/register')
def register_page():
    return render_template('register.html')

@views_bp.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@views_bp.route('/doctor_dashboard')
def doctor_dashboard():
    return render_template('doctor_dashboard.html')

@views_bp.route('/admin_dashboard')
def admin_dashboard():
    return render_template('admin_dashboard.html')

@views_bp.route('/nuevo_usuario')
def nuevo_usuario():
    return render_template('nuevo_usuario.html')

@views_bp.route('/nueva_cita')
def nueva_cita():
    return render_template('nueva_cita.html')

@views_bp.route('/pacientes')
def pacientes():
    return render_template('pacientes.html')

@views_bp.route('/medicos')
def medicos():
    return render_template('medicos.html')

@views_bp.route('/horarios')
def horarios():
    return render_template('horarios.html')

@views_bp.route('/users')
def users():
    return render_template('users.html')
