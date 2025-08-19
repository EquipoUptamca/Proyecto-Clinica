from flask import Blueprint, request, jsonify
import pyodbc
import logging
import secrets
import smtplib
from database import get_db_connection
from werkzeug.security import generate_password_hash, check_password_hash
import re  # For email validation
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

users_bp = Blueprint('users', __name__)

# Validaciones comunes
def validate_user_data(data, is_update=False):
    # Campos requeridos
    required_fields = ['nombre_completo', 'usuario_login', 'id_rol', 'cedula']
    
    # Solo requerir contraseña para creación
    if not is_update:
        required_fields.append('contraseña')
    
    # Verificar campos requeridos
    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
        return {'error': f'Faltan campos requeridos: {", ".join(missing_fields)}'}, 400

    # Validaciones de longitud
    if len(data['usuario_login']) > 50:
        return {'error': 'El nombre de usuario no puede exceder 50 caracteres'}, 400
        
    if len(data['nombre_completo']) > 100:
        return {'error': 'El nombre completo no puede exceder 100 caracteres'}, 400
        
    if not is_update and 'contraseña' in data and len(data['contraseña']) < 8:
        return {'error': 'La contraseña debe tener al menos 8 caracteres'}, 400

    # Validar formato de email si se proporciona
    if 'gmail' in data and data['gmail']:
        if not re.match(r"[^@]+@[^@]+\.[^@]+", data['gmail']):
            return {'error': 'El formato del email no es válido'}, 400

    # Validar formato de cédula (8 dígitos numéricos)
    if not str(data['cedula']).isdigit() or len(str(data['cedula'])) != 8:
        return {'error': 'La cédula debe tener 8 dígitos numéricos'}, 400

    # Validar teléfono si se proporciona
    if 'telefono' in data and data['telefono']:
        if not str(data['telefono']).isdigit() or len(str(data['telefono'])) < 7 or len(str(data['telefono'])) > 12:
            return {'error': 'El teléfono debe tener entre 7 y 10 dígitos'}, 400

    return None

# Obtener lista de usuarios
@users_bp.route('/api/users', methods=['GET'])
def get_users():
    # Parámetros de paginación y filtrado
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    search = request.args.get('search', '')
    role_id = request.args.get('role_id', type=int)
    status = request.args.get('status', type=int)  # 1=activo, 0=inactivo

    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Error de conexión a la base de datos'}), 500

    cursor = None
    try:
        cursor = conn.cursor()

        # Construir consulta base
        query = """
            SELECT id_usuario, nombre_completo, usuario_login, cedula, telefono, gmail, id_rol, activo
            FROM usuarios
            WHERE 1=1
        """
        params = []

        # Aplicar filtros
        if search:
            query += " AND (nombre_completo LIKE ? OR usuario_login LIKE ? OR cedula LIKE ?)"
            search_term = f"%{search}%"
            params.extend([search_term, search_term, search_term])

        if role_id is not None:
            query += " AND id_rol = ?"
            params.append(role_id)

        if status is not None:
            query += " AND activo = ?"
            params.append(bool(status))

        # Contar total de registros
        count_query = f"SELECT COUNT(*) FROM ({query}) AS total"
        cursor.execute(count_query, params)
        total_users = cursor.fetchone()[0]

        # Aplicar paginación
        query += " ORDER BY nombre_completo OFFSET ? ROWS FETCH NEXT ? ROWS ONLY"
        params.extend([(page - 1) * per_page, per_page])

        cursor.execute(query, params)
        users = cursor.fetchall()

        # Formatear resultados
        users_list = []
        for user in users:
            users_list.append({
                'id_usuario': user[0],
                'nombre_completo': user[1],
                'usuario_login': user[2],
                'cedula': user[3],
                'telefono': user[4],
                'gmail': user[5],
                'id_rol': user[6],
                'activo': bool(user[7])  # Convertir a booleano
            })

        return jsonify({
            'users': users_list,
            'total': total_users,
            'page': page,
            'per_page': per_page,
            'total_pages': (total_users + per_page - 1) // per_page
        })

    except pyodbc.Error as e:
        logging.error(f"Database error in get_users: {str(e)}")
        return jsonify({'error': 'Error al obtener usuarios', 'details': str(e)}), 500
    except Exception as e:
        logging.error(f"Unexpected error in get_users: {str(e)}")
        return jsonify({'error': 'Error inesperado al obtener usuarios'}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# Obtener un usuario específico
@users_bp.route('/api/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Error de conexión a la base de datos'}), 500

    cursor = None
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id_usuario, nombre_completo, usuario_login, cedula, telefono, gmail, id_rol, activo
            FROM usuarios
            WHERE id_usuario = ?
        """, (user_id,))
        
        user = cursor.fetchone()
        if not user:
            return jsonify({'error': 'Usuario no encontrado'}), 404

        return jsonify({
            'id_usuario': user[0],
            'nombre_completo': user[1],
            'usuario_login': user[2],
            'cedula': user[3],
            'telefono': user[4],
            'gmail': user[5],
            'id_rol': user[6],
            'activo': bool(user[7])  # Convertir a booleano
        })

    except pyodbc.Error as e:
        logging.error(f"Database error in get_user: {str(e)}")
        return jsonify({'error': 'Error al obtener el usuario', 'details': str(e)}), 500
    except Exception as e:
        logging.error(f"Unexpected error in get_user: {str(e)}")
        return jsonify({'error': 'Error inesperado al obtener el usuario'}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# Crear un nuevo usuario
@users_bp.route('/api/users', methods=['POST'])
def create_user():
    # Verificar que se envió JSON
    if not request.is_json:
        return jsonify({'error': 'Se esperaba contenido tipo JSON'}), 400
    
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Datos JSON no proporcionados o inválidos'}), 400
    
    # Validar datos
    validation_error = validate_user_data(data)
    if validation_error:
        return jsonify(validation_error[0]), validation_error[1]

    # Generar hash de contraseña
    hashed_password = generate_password_hash(
        data['contraseña'],
        method='pbkdf2:sha256',
        salt_length=16
    )

    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Error de conexión a la base de datos'}), 500

    cursor = None
    try:
        cursor = conn.cursor()

        # Verificar si el usuario o cédula ya existen
        cursor.execute("""
            SELECT 1 FROM usuarios 
            WHERE usuario_login = ? OR cedula = ?
        """, (data['usuario_login'], data['cedula']))

        if cursor.fetchone():
            return jsonify({'error': 'El nombre de usuario o cédula ya están en uso'}), 400

        # Insertar nuevo usuario
        cursor.execute("""
            INSERT INTO usuarios (
                nombre_completo, usuario_login, contraseña, id_rol, 
                cedula, telefono, gmail, activo
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data['nombre_completo'],
            data['usuario_login'],
            hashed_password,
            int(data['id_rol']),  # Asegurar que es entero
            str(data['cedula']),  # Asegurar que es string
            data.get('telefono'),
            data.get('gmail'),
            bool(data.get('activo', True))  # Por defecto activo
        ))

        conn.commit()

        # Obtener ID del nuevo usuario
        cursor.execute("SELECT SCOPE_IDENTITY()")
        new_user_id = cursor.fetchone()[0]

        return jsonify({
            'message': 'Usuario creado exitosamente',
            'id_usuario': new_user_id
        }), 201

    except pyodbc.Error as e:
        conn.rollback()
        logging.error(f"Database error in create_user: {str(e)}")
        return jsonify({'error': 'Error al crear el usuario', 'details': str(e)}), 500
    except Exception as e:
        conn.rollback()
        logging.error(f"Unexpected error in create_user: {str(e)}")
        return jsonify({'error': 'Error inesperado al crear el usuario'}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# Actualizar un usuario existente
@users_bp.route('/api/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    # Verificar que se envió JSON y obtener datos
    if not request.is_json:
        logging.error("Solicitud PUT sin contenido JSON")
        return jsonify({'error': 'Se esperaba contenido tipo JSON'}), 400
    
    try:
        data = request.get_json()
    except Exception as e:
        logging.error(f"Error al parsear JSON: {str(e)}")
        return jsonify({'error': 'Datos JSON no válidos'}), 400
    
    if not data:
        logging.error("Datos JSON vacíos")
        return jsonify({'error': 'Datos JSON no proporcionados'}), 400
    
    # Loggear datos recibidos para diagnóstico
    logging.info(f"Datos recibidos para actualización de usuario {user_id}: {data}")
    
    # Validar datos (sin requerir contraseña para actualización)
    validation_error = validate_user_data(data, is_update=True)
    if validation_error:
        logging.error(f"Error de validación: {validation_error[0]}")
        return jsonify(validation_error[0]), validation_error[1]

    conn = get_db_connection()
    if not conn:
        logging.error("Error de conexión a la base de datos")
        return jsonify({'error': 'Error de conexión a la base de datos'}), 500

    cursor = None
    try:
        cursor = conn.cursor()

        # Verificar si el usuario existe
        cursor.execute("SELECT usuario_login, cedula FROM usuarios WHERE id_usuario = ?", (user_id,))
        existing_user = cursor.fetchone()
        
        if not existing_user:
            logging.error(f"Usuario con ID {user_id} no encontrado")
            return jsonify({'error': 'Usuario no encontrado'}), 404

        current_username, current_cedula = existing_user

        # Verificar si el nuevo usuario_login o cédula ya están en uso por otro usuario
        if ('usuario_login' in data and data['usuario_login'] != current_username) or \
           ('cedula' in data and data['cedula'] != current_cedula):
            
            cursor.execute("""
                SELECT 1 FROM usuarios 
                WHERE id_usuario != ? AND (usuario_login = ? OR cedula = ?)
            """, (user_id, 
                 data.get('usuario_login', current_username), 
                 data.get('cedula', current_cedula)))

            if cursor.fetchone():
                error_msg = 'El nombre de usuario o cédula ya están en uso por otro usuario'
                logging.error(error_msg)
                return jsonify({'error': error_msg}), 400

        # Construir consulta de actualización
        update_fields = []
        params = []
        
        if 'nombre_completo' in data:
            update_fields.append("nombre_completo = ?")
            params.append(data['nombre_completo'])
        
        if 'usuario_login' in data:
            update_fields.append("usuario_login = ?")
            params.append(data['usuario_login'])
        
        if 'id_rol' in data:
            update_fields.append("id_rol = ?")
            params.append(int(data['id_rol']))
        
        if 'cedula' in data:
            update_fields.append("cedula = ?")
            params.append(str(data['cedula']))
        
        if 'telefono' in data:
            update_fields.append("telefono = ?")
            params.append(data['telefono'] if data['telefono'] else None)
        
        if 'gmail' in data:
            update_fields.append("gmail = ?")
            params.append(data['gmail'] if data['gmail'] else None)
        
        if 'activo' in data:
            update_fields.append("activo = ?")
            params.append(bool(data['activo']))
        
        # Actualizar contraseña solo si se proporciona
        if 'contraseña' in data and data['contraseña']:
            hashed_password = generate_password_hash(data['contraseña'], method='pbkdf2:sha256', salt_length=16)
            update_fields.append("contraseña = ?")
            params.append(hashed_password)

        # Si no hay campos para actualizar
        if not update_fields:
            logging.error("No se proporcionaron campos para actualizar")
            return jsonify({'error': 'No se proporcionaron campos para actualizar'}), 400

        params.append(user_id)  # Para el WHERE

        update_query = f"""
            UPDATE usuarios
            SET {', '.join(update_fields)}
            WHERE id_usuario = ?
        """

        logging.info(f"Ejecutando consulta: {update_query} con parámetros: {params}")
        cursor.execute(update_query, params)
        conn.commit()

        return jsonify({'message': 'Usuario actualizado exitosamente'})

    except pyodbc.Error as e:
        conn.rollback()
        error_msg = f"Database error in update_user: {str(e)}"
        logging.error(error_msg)
        return jsonify({
            'error': 'Error al actualizar el usuario',
            'details': str(e)
        }), 500
    except Exception as e:
        conn.rollback()
        error_msg = f"Unexpected error in update_user: {str(e)}"
        logging.error(error_msg)
        return jsonify({
            'error': 'Error inesperado al actualizar el usuario',
            'details': str(e)
        }), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# Eliminar un usuario (o cambiar estado)
@users_bp.route('/api/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Error de conexión a la base de datos'}), 500

    cursor = None
    try:
        cursor = conn.cursor()

        # Verificar si el usuario existe
        cursor.execute("SELECT 1 FROM usuarios WHERE id_usuario = ?", (user_id,))
        if not cursor.fetchone():
            return jsonify({'error': 'Usuario no encontrado'}), 404

        # Cambiar estado a inactivo
        cursor.execute("""
            UPDATE usuarios
            SET activo = 0
            WHERE id_usuario = ?
        """, (user_id,))

        conn.commit()

        return jsonify({'message': 'Usuario desactivado exitosamente'})

    except pyodbc.Error as e:
        conn.rollback()
        logging.error(f"Database error in delete_user: {str(e)}")
        return jsonify({
            'error': 'Error al desactivar el usuario',
            'details': str(e)
        }), 500
    except Exception as e:
        conn.rollback()
        logging.error(f"Unexpected error in delete_user: {str(e)}")
        return jsonify({
            'error': 'Error inesperado al desactivar el usuario',
            'details': str(e)
        }), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
@users_bp.route('/api/password-recovery', methods=['POST'])
def request_password_recovery():
    if not request.is_json:
        return jsonify({'error': 'Se esperaba contenido tipo JSON'}), 400
    
    data = request.get_json()
    if not data or 'identificador' not in data:
        return jsonify({'error': 'Se requiere un identificador (usuario o email)'}), 400
    
    identificador = data['identificador'].strip()
    
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Error de conexión a la base de datos'}), 500

    cursor = None
    try:
        cursor = conn.cursor()
        
        # Buscar usuario por nombre de usuario o email
        cursor.execute("""
            SELECT id_usuario, usuario_login, gmail 
            FROM usuarios 
            WHERE usuario_login = ? OR gmail = ?
        """, (identificador, identificador))
        
        user = cursor.fetchone()
        if not user:
            return jsonify({'error': 'No se encontró usuario con ese identificador'}), 404
        
        user_id, username, email = user
        
        # Generar token de recuperación (válido por 1 hora)
        token = secrets.token_urlsafe(32)
        expiration = datetime.now() + timedelta(hours=1)
        
        # Guardar token en la base de datos
        cursor.execute("""
            INSERT INTO password_reset_tokens (user_id, token, expiration)
            VALUES (?, ?, ?)
        """, (user_id, token, expiration))
        
        conn.commit()
        
        # Enviar email con el enlace de recuperación (implementación básica)
        if email:
            send_recovery_email(email, username, token)
        
        return jsonify({
            'message': 'Se han enviado instrucciones para recuperar la contraseña',
            'email_sent': bool(email)
        })
        
    except pyodbc.Error as e:
        conn.rollback()
        logging.error(f"Database error in password recovery: {str(e)}")
        return jsonify({'error': 'Error al procesar la solicitud'}), 500
    except Exception as e:
        conn.rollback()
        logging.error(f"Unexpected error in password recovery: {str(e)}")
        return jsonify({'error': 'Error inesperado al procesar la solicitud'}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@users_bp.route('/api/reset-password', methods=['POST'])
def reset_password():
    if not request.is_json:
        logging.error("Reset password request without JSON")
        return jsonify({'error': 'Se esperaba contenido tipo JSON'}), 400
    
    data = request.get_json()
    if not data:
        logging.error("Empty JSON data in reset password")
        return jsonify({'error': 'Datos JSON no proporcionados'}), 400
    
    # Validar campos requeridos
    if 'token' not in data:
        logging.error("Token missing in reset password request")
        return jsonify({'error': 'Token es requerido'}), 400
        
    if 'nueva_contraseña' not in data:
        logging.error("New password missing in reset password request")
        return jsonify({'error': 'Nueva contraseña es requerida'}), 400
    
    token = data['token']
    new_password = data['nueva_contraseña']
    
    # Validar longitud de contraseña
    if len(new_password) < 8:
        logging.error("Password too short in reset request")
        return jsonify({'error': 'La contraseña debe tener al menos 8 caracteres'}), 400
    
    conn = get_db_connection()
    if not conn:
        logging.error("Database connection failed in reset password")
        return jsonify({'error': 'Error de conexión a la base de datos'}), 500

    cursor = None
    try:
        cursor = conn.cursor()
        
        # Verificar token válido y no expirado
        cursor.execute("""
            SELECT user_id, expiration 
            FROM password_reset_tokens 
            WHERE token = ? AND used = 0 AND expiration > ?
        """, (token, datetime.now()))
        
        token_data = cursor.fetchone()
        if not token_data:
            logging.error(f"Invalid or expired token: {token}")
            return jsonify({
                'error': 'Token inválido o expirado. Por favor solicite un nuevo enlace de recuperación.',
                'code': 'invalid_token'
            }), 400
        
        user_id, expiration = token_data
        
        # Resto de la lógica para actualizar contraseña...
        
    except Exception as e:
        logging.error(f"Error in reset password: {str(e)}")
        return jsonify({'error': 'Error interno al procesar la solicitud'}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
def send_recovery_email(to_email, username, token):
    # Configuración básica de email (debes personalizar esto)
    sender_email = "equipo.uptamca.clinica@gmail.com"
    subject = "Recuperación de contraseña - Sistema Clínico"
    
    reset_link = f"https://tuclinica.com/reset-password?token={token}"
    
    # Cuerpo del email
    body = f"""
    <html>
    <body>
        <h2>Recuperación de contraseña</h2>
        <p>Hola {username},</p>
        <p>Hemos recibido una solicitud para restablecer tu contraseña. Si no realizaste esta solicitud, puedes ignorar este mensaje.</p>
        <p>Para crear una nueva contraseña, haz clic en el siguiente enlace (válido por 1 hora):</p>
        <p><a href="{reset_link}">{reset_link}</a></p>
        <p>Si el enlace no funciona, copia y pega la URL en tu navegador.</p>
        <br>
        <p>Atentamente,</p>
        <p>El equipo de Sistema Clínico</p>
    </body>
    </html>
    """
    
    try:
        # Configura el mensaje
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'html'))
        
        # Envía el email (configura tu servidor SMTP)
        with smtplib.SMTP('smtp.tuproveedor.com', 587) as server:
            server.starttls()
            server.login(sender_email, "tu_contraseña")
            server.send_message(msg)
            
        logging.info(f"Recovery email sent to {to_email}")
    except Exception as e:
        logging.error(f"Error sending recovery email: {str(e)}")