from flask import Blueprint, request, jsonify, url_for
import pyodbc
import logging
from database import get_db_connection
from werkzeug.security import generate_password_hash, check_password_hash

auth_bp = Blueprint('auth', __name__)

# API to get roles
@auth_bp.route('/api/roles', methods=['GET'])
def get_roles():
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
        
    cursor = None
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id_rol, nombre_rol FROM roles ORDER BY id_rol")
        roles = cursor.fetchall()
        
        return jsonify([{'id_rol': r[0], 'nombre_rol': r[1]} for r in roles])
    except pyodbc.Error as e:
        logging.error(f"Database error in get_roles: {str(e)}")
        return jsonify({'error': 'Failed to fetch roles'}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

# API for registration
@auth_bp.route('/api/register', methods=['POST'])
def register():
    data = request.json
    required_fields = ['nombre_completo', 'usuario_login', 'contraseña', 'id_rol']
    
    # Validación de campos requeridos
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Faltan campos requeridos'}), 400

    # Validación de longitud de inputs
    if len(data['usuario_login']) > 50:
        return jsonify({'error': 'El nombre de usuario no puede exceder 50 caracteres'}), 400
        
    if len(data['nombre_completo']) > 100:
        return jsonify({'error': 'El nombre completo no puede exceder 100 caracteres'}), 400
        
    if len(data['contraseña']) < 8:
        return jsonify({'error': 'La contraseña debe tener al menos 8 caracteres'}), 400

    # Generar hash seguro de la contraseña (versión corregida)
    try:
        hashed_password = generate_password_hash(
            data['contraseña'],
            method='pbkdf2:sha256'
        )
        
        # Registrar longitud del hash para diagnóstico
        logging.info(f"Longitud del hash generado: {len(hashed_password)}")
        
    except Exception as e:
        logging.error(f"Error al generar hash: {str(e)}")
        return jsonify({'error': 'Error interno al procesar la contraseña'}), 500

    # Resto del código de conexión a la base de datos...
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Error de conexión con la base de datos'}), 500
        
    cursor = None
    try:
        cursor = conn.cursor()
        
        # Verificar si el usuario ya existe
        cursor.execute("SELECT 1 FROM usuarios WHERE usuario_login = ?", 
                       (data['usuario_login'],))
        if cursor.fetchone():
            return jsonify({'error': 'El nombre de usuario ya existe'}), 400
            
        # Insertar nuevo usuario
        cursor.execute("""
            INSERT INTO usuarios (nombre_completo, usuario_login, contraseña, id_rol)
            VALUES (?, ?, ?, ?)
        """, (
            data['nombre_completo'], 
            data['usuario_login'], 
            hashed_password, 
            data['id_rol']
        ))
        
        conn.commit()
        
        return jsonify({
            'message': 'Usuario registrado exitosamente',
            'redirect': url_for('views.login_page')
        }), 201
        
    except pyodbc.Error as e:
        conn.rollback()
        logging.error(f"Error de base de datos en registro: {str(e)}")
        return jsonify({'error': 'Error en el registro. Por favor intente nuevamente.'}), 500
            
    except Exception as e:
        conn.rollback()
        logging.error(f"Error inesperado en registro: {str(e)}")
        return jsonify({'error': 'Error interno del servidor'}), 500
        
    finally:
        if cursor: 
            cursor.close()
        if conn: 
            conn.close()

# API for login
@auth_bp.route('/api/login', methods=['POST'])
def login():
    data = request.json
    # Permitir login con usuario o cédula
    required_fields = ['identificador', 'contraseña']
    
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Faltan campos requeridos'}), 400

    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Error de conexión con la base de datos'}), 500
        
    cursor = None
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id_usuario, nombre_completo, id_rol, contraseña, cedula 
            FROM usuarios 
            WHERE usuario_login = ? OR cedula = ?
        """, (data['identificador'], data['identificador']))
        
        user = cursor.fetchone()
        if user and check_password_hash(user[3], data['contraseña']):
            # Determine redirect based on role
            if user[2] == 1:  # Admin
                redirect_url = url_for('views.admin_dashboard')
            elif user[2] == 2:  # Doctor
                redirect_url = url_for('views.doctor_dashboard')
            else:
                redirect_url = url_for('views.dashboard')
                
            return jsonify({
                'message': 'Inicio de sesión exitoso',
                'id_usuario': user[0],
                'nombre_completo': user[1],
                'id_rol': user[2],
                'cedula': user[4],
                'redirect': redirect_url
            }), 200
        else:
            return jsonify({'error': 'Credenciales inválidas'}), 401
    except pyodbc.Error as e:
        logging.error(f"Error de base de datos en login: {str(e)}")
        return jsonify({'error': 'Error en el inicio de sesión'}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()