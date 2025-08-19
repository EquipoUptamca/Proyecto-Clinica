from flask import Blueprint, request, jsonify
import pyodbc
import logging
from datetime import datetime
from database import get_db_connection

patients_bp = Blueprint('patients', __name__)
logger = logging.getLogger(__name__)

# Endpoint para obtener pacientes
@patients_bp.route('/api/pacientes', methods=['GET'])
def get_pacientes():
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Error de conexión a la base de datos'}), 500
        
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT id_paciente, nombre_completo 
                FROM pacientes 
                ORDER BY nombre_completo
            """)
            pacientes = [{
                'id_paciente': row[0],
                'nombre_completo': row[1]
            } for row in cursor.fetchall()]
            
            return jsonify(pacientes)
    except pyodbc.Error as e:
        logging.error(f"Error en base de datos: {str(e)}")
        return jsonify({'error': 'Error al obtener pacientes'}), 500
    finally:
        conn.close()

# Cambia el nombre de la segunda función get_pacientes a get_pacientes_detallados
@patients_bp.route('/api/pacientes/detallados', methods=['GET'])
def get_pacientes_detallados():
    """Obtiene todos los pacientes con opciones de filtrado"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Error de conexión a la base de datos'}), 500

    try:
        # Obtener parámetros de filtrado
        estado = request.args.get('estado')
        search = request.args.get('search')
        fecha_desde = request.args.get('fecha_desde')
        fecha_hasta = request.args.get('fecha_hasta')

        with conn.cursor() as cursor:
            # Construir consulta base
            query = """
                SELECT 
                    id_paciente, nombre_completo, telefono, correo, 
                    direccion, cedula, estado, fecha_nacimiento,
                    genero, tipo_sangre, observaciones, fecha_creacion
                FROM pacientes
                WHERE 1=1
            """
            params = []

            # Aplicar filtros
            if estado:
                query += " AND estado = ?"
                params.append(estado)
            
            if search:
                query += """
                    AND (nombre_completo LIKE ? OR 
                         telefono LIKE ? OR 
                         cedula LIKE ? OR 
                         correo LIKE ?)
                """
                search_term = f"%{search}%"
                params.extend([search_term, search_term, search_term, search_term])
            
            if fecha_desde:
                query += " AND fecha_creacion >= ?"
                params.append(fecha_desde)
            
            if fecha_hasta:
                query += " AND fecha_creacion <= ?"
                params.append(fecha_hasta)

            query += " ORDER BY nombre_completo"

            cursor.execute(query, params)
            
            pacientes = [{
                'id_paciente': row[0],
                'nombre_completo': row[1],
                'telefono': row[2],
                'correo': row[3],
                'direccion': row[4],
                'cedula': row[5],
                'estado': row[6],
                'fecha_nacimiento': row[7].strftime('%Y-%m-%d') if row[7] else None,
                'genero': row[8],
                'tipo_sangre': row[9],
                'observaciones': row[10],
                'fecha_creacion': row[11].strftime('%Y-%m-%d %H:%M:%S') if row[11] else None
            } for row in cursor.fetchall()]
            
            return jsonify(pacientes)
    except pyodbc.Error as e:
        logger.error(f"Error en la base de datos: {str(e)}")
        return jsonify({'error': 'Error al obtener pacientes'}), 500
    finally:
        conn.close()

@patients_bp.route('/api/pacientes/stats', methods=['GET'])
def get_pacientes_stats():
    """Obtiene estadísticas de pacientes"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Error de conexión a la base de datos'}), 500

    try:
        with conn.cursor() as cursor:
            # Total pacientes activos
            cursor.execute("SELECT COUNT(*) FROM pacientes WHERE estado = 'A'")
            active = cursor.fetchone()[0]
            
            # Total pacientes
            cursor.execute("SELECT COUNT(*) FROM pacientes")
            total = cursor.fetchone()[0]
            
            # Nuevos este mes
            cursor.execute("""
                SELECT COUNT(*) FROM pacientes 
                WHERE fecha_creacion >= DATEADD(month, DATEDIFF(month, 0, GETDATE()), 0)
            """)
            new_this_month = cursor.fetchone()[0]
            
            return jsonify({
                'active': active,
                'total': total,
                'new_this_month': new_this_month
            })
    except pyodbc.Error as e:
        logger.error(f"Error en la base de datos: {str(e)}")
        return jsonify({'error': 'Error al obtener estadísticas'}), 500
    finally:
        conn.close()

@patients_bp.route('/api/pacientes/check-cedula', methods=['GET'])
def check_cedula():
    """Verifica si una cédula ya está registrada"""
    cedula = request.args.get('cedula')
    exclude = request.args.get('exclude')
    
    if not cedula:
        return jsonify({'error': 'Se requiere el parámetro cedula'}), 400

    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Error de conexión a la base de datos'}), 500

    try:
        with conn.cursor() as cursor:
            if exclude:
                cursor.execute(
                    "SELECT 1 FROM pacientes WHERE cedula = ? AND id_paciente != ?", 
                    (cedula, exclude)
                )
            else:
                cursor.execute(
                    "SELECT 1 FROM pacientes WHERE cedula = ?", 
                    (cedula,)
                )
            
            exists = cursor.fetchone() is not None
            return jsonify({'exists': exists})
    except pyodbc.Error as e:
        logger.error(f"Error en la base de datos: {str(e)}")
        return jsonify({'error': 'Error al verificar cédula'}), 500
    finally:
        conn.close()

@patients_bp.route('/api/pacientes', methods=['POST'])
def create_paciente():
    """Crea un nuevo paciente"""
    data = request.json
    required_fields = ['nombre_completo', 'estado', 'cedula']
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Faltan campos requeridos'}), 400

    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Error de conexión a la base de datos'}), 500

    try:
        with conn.cursor() as cursor:
            # Verificar cédula única
            cursor.execute("SELECT 1 FROM pacientes WHERE cedula = ?", (data['cedula'],))
            if cursor.fetchone():
                return jsonify({'error': 'La cédula ya está registrada'}), 400

            cursor.execute("""
                INSERT INTO pacientes (
                    nombre_completo, 
                    fecha_nacimiento,
                    telefono, 
                    correo, 
                    direccion,
                    cedula,
                    estado,
                    genero,
                    tipo_sangre,
                    observaciones,
                    fecha_creacion
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, GETDATE())
            """, (
                data['nombre_completo'],
                data.get('fecha_nacimiento'),
                data.get('telefono'),
                data.get('correo'),
                data.get('direccion'),
                data['cedula'],
                data['estado'],
                data.get('genero'),
                data.get('tipo_sangre'),
                data.get('observaciones')
            ))
            
            conn.commit()
            paciente_id = cursor.execute("SELECT SCOPE_IDENTITY()").fetchone()[0]
            
            return jsonify({
                'message': 'Paciente creado exitosamente',
                'id_paciente': paciente_id
            }), 201
    except pyodbc.Error as e:
        conn.rollback()
        logger.error(f"Error en la base de datos: {str(e)}")
        return jsonify({'error': 'Error al crear paciente'}), 500
    finally:
        conn.close()

@patients_bp.route('/api/pacientes/<int:id_paciente>', methods=['GET'])
def get_paciente(id_paciente):
    """Obtiene un paciente específico por ID"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Error de conexión a la base de datos'}), 500

    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    id_paciente, nombre_completo, fecha_nacimiento, telefono, 
                    correo, direccion, cedula, estado, genero, tipo_sangre,
                    observaciones, fecha_creacion, fecha_actualizacion
                FROM pacientes 
                WHERE id_paciente = ?
            """, (id_paciente,))
            
            row = cursor.fetchone()
            if not row:
                return jsonify({'error': 'Paciente no encontrado'}), 404
                
            paciente = {
                'id_paciente': row[0],
                'nombre_completo': row[1],
                'fecha_nacimiento': row[2].strftime('%Y-%m-%d') if row[2] else None,
                'telefono': row[3],
                'correo': row[4],
                'direccion': row[5],
                'cedula': row[6],
                'estado': row[7],
                'genero': row[8],
                'tipo_sangre': row[9],
                'observaciones': row[10],
                'fecha_creacion': row[11].strftime('%Y-%m-%d %H:%M:%S') if row[11] else None,
                'fecha_actualizacion': row[12].strftime('%Y-%m-%d %H:%M:%S') if row[12] else None
            }
            
            return jsonify(paciente)
    except pyodbc.Error as e:
        logger.error(f"Error en la base de datos: {str(e)}")
        return jsonify({'error': 'Error al obtener paciente'}), 500
    finally:
        conn.close()

@patients_bp.route('/api/pacientes/<int:id_paciente>', methods=['PUT'])
def update_paciente(id_paciente):
    """Actualiza un paciente existente"""
    data = request.json
    required_fields = ['nombre_completo', 'estado', 'cedula']
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Faltan campos requeridos'}), 400

    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Error de conexión a la base de datos'}), 500

    try:
        with conn.cursor() as cursor:
            # Verificar cédula única excluyendo el paciente actual
            cursor.execute("""
                SELECT 1 FROM pacientes 
                WHERE cedula = ? AND id_paciente != ?
            """, (data['cedula'], id_paciente))
            
            if cursor.fetchone():
                return jsonify({'error': 'La cédula ya está registrada para otro paciente'}), 400

            cursor.execute("""
                UPDATE pacientes SET
                    nombre_completo = ?,
                    fecha_nacimiento = ?,
                    telefono = ?,
                    correo = ?,
                    direccion = ?,
                    cedula = ?,
                    estado = ?,
                    genero = ?,
                    tipo_sangre = ?,
                    observaciones = ?,
                    fecha_actualizacion = GETDATE()
                WHERE id_paciente = ?
            """, (
                data['nombre_completo'],
                data.get('fecha_nacimiento'),
                data.get('telefono'),
                data.get('correo'),
                data.get('direccion'),
                data['cedula'],
                data['estado'],
                data.get('genero'),
                data.get('tipo_sangre'),
                data.get('observaciones'),
                id_paciente
            ))
            
            if cursor.rowcount == 0:
                return jsonify({'error': 'Paciente no encontrado'}), 404
                
            conn.commit()
            return jsonify({'message': 'Paciente actualizado exitosamente'})
    except pyodbc.Error as e:
        conn.rollback()
        logger.error(f"Error en la base de datos: {str(e)}")
        return jsonify({'error': 'Error al actualizar paciente'}), 500
    finally:
        conn.close()

@patients_bp.route('/api/pacientes/<int:id_paciente>/status', methods=['PATCH'])
def update_paciente_status(id_paciente):
    """Actualiza solo el estado de un paciente"""
    data = request.json
    if 'estado' not in data:
        return jsonify({'error': 'Se requiere el campo estado'}), 400

    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Error de conexión a la base de datos'}), 500

    try:
        with conn.cursor() as cursor:
            # Si se está inactivando, verificar citas futuras
            if data['estado'] == 'I':
                cursor.execute("""
                    SELECT 1 FROM citas 
                    WHERE id_paciente = ? AND fecha_cita >= CAST(GETDATE() AS DATE)
                """, (id_paciente,))
                
                if cursor.fetchone():
                    return jsonify({
                        'error': 'No se puede inactivar el paciente porque tiene citas programadas'
                    }), 400

            cursor.execute("""
                UPDATE pacientes SET
                    estado = ?,
                    fecha_actualizacion = GETDATE()
                WHERE id_paciente = ?
            """, (data['estado'], id_paciente))
            
            if cursor.rowcount == 0:
                return jsonify({'error': 'Paciente no encontrado'}), 404
                
            conn.commit()
            return jsonify({
                'message': f"Paciente marcado como {'activo' if data['estado'] == 'A' else 'inactivo'} exitosamente"
            })
    except pyodbc.Error as e:
        conn.rollback()
        logger.error(f"Error en la base de datos: {str(e)}")
        return jsonify({'error': 'Error al actualizar estado del paciente'}), 500
    finally:
        conn.close()

@patients_bp.route('/api/pacientes/<int:id_paciente>', methods=['DELETE'])
def delete_paciente(id_paciente):
    """Marca un paciente como inactivo (eliminación lógica)"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Error de conexión a la base de datos'}), 500

    try:
        with conn.cursor() as cursor:
            # Verificar citas futuras antes de inactivar
            cursor.execute("""
                SELECT 1 FROM citas 
                WHERE id_paciente = ? AND fecha_cita >= CAST(GETDATE() AS DATE)
            """, (id_paciente,))
            
            if cursor.fetchone():
                return jsonify({
                    'error': 'No se puede inactivar el paciente porque tiene citas programadas'
                }), 400

            cursor.execute("""
                UPDATE pacientes SET
                    estado = 'I',
                    fecha_actualizacion = GETDATE()
                WHERE id_paciente = ?
            """, (id_paciente,))
            
            if cursor.rowcount == 0:
                return jsonify({'error': 'Paciente no encontrado'}), 404
                
            conn.commit()
            return jsonify({'message': 'Paciente marcado como inactivo exitosamente'})
    except pyodbc.Error as e:
        conn.rollback()
        logger.error(f"Error en la base de datos: {str(e)}")
        return jsonify({'error': 'Error al inactivar paciente'}), 500
    finally:
        conn.close()