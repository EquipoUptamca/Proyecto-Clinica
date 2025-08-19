from flask import Blueprint, request, jsonify
import pyodbc
import logging
from database import get_db_connection

doctors_bp = Blueprint('doctors', __name__)

# Endpoint para obtener médicos disponibles
@doctors_bp.route('/api/medicos/disponibles', methods=['GET'])
def get_medicos_disponibles():
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Error de conexión a la base de datos'}), 500
        
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT id_medico, nombre_completo, especialidad 
                FROM medicos 
                WHERE estado = 'A'
                ORDER BY nombre_completo
            """)
            medicos = [{
                'id_medico': row[0],
                'nombre_completo': row[1],
                'especialidad': row[2]
            } for row in cursor.fetchall()]
            
            return jsonify(medicos)
    except pyodbc.Error as e:
        logging.error(f"Error en base de datos: {str(e)}")
        return jsonify({'error': 'Error al obtener médicos'}), 500
    finally:
        conn.close()

# Endpoint para obtener todos los médicos
@doctors_bp.route('/api/medicos', methods=['GET'])
def get_medicos():
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Error de conexión a la base de datos'}), 500
        
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT id_medico, nombre_completo, especialidad, telefono, correo, estado 
                FROM medicos
                ORDER BY nombre_completo
            """)
            medicos = [{
                'id_medico': row[0],
                'nombre_completo': row[1],
                'especialidad': row[2],
                'telefono': row[3],
                'correo': row[4],
                'estado': row[5]
            } for row in cursor.fetchall()]
            
            return jsonify(medicos)
    except pyodbc.Error as e:
        logging.error(f"Error en base de datos: {str(e)}")
        return jsonify({'error': 'Error al obtener médicos'}), 500
    finally:
        conn.close()

# Endpoint para obtener especialidades únicas
@doctors_bp.route('/api/medicos/especialidades', methods=['GET'])
def get_especialidades():
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Error de conexión a la base de datos'}), 500
        
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT DISTINCT especialidad 
                FROM medicos 
                WHERE especialidad IS NOT NULL
                ORDER BY especialidad
            """)
            especialidades = [row[0] for row in cursor.fetchall()]
            return jsonify(especialidades)
    except pyodbc.Error as e:
        logging.error(f"Error en base de datos: {str(e)}")
        return jsonify({'error': 'Error al obtener especialidades'}), 500
    finally:
        conn.close()

# Endpoint para obtener un médico específico
@doctors_bp.route('/api/medicos/<int:id_medico>', methods=['GET'])
def get_medico(id_medico):
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Error de conexión a la base de datos'}), 500
        
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT id_medico, nombre_completo, especialidad, telefono, correo, estado 
                FROM medicos 
                WHERE id_medico = ?
            """, (id_medico,))
            
            row = cursor.fetchone()
            if not row:
                return jsonify({'error': 'Médico no encontrado'}), 404
                
            medico = {
                'id_medico': row[0],
                'nombre_completo': row[1],
                'especialidad': row[2],
                'telefono': row[3],
                'correo': row[4],
                'estado': row[5]
            }
            
            return jsonify(medico)
    except pyodbc.Error as e:
        logging.error(f"Error en base de datos: {str(e)}")
        return jsonify({'error': 'Error al obtener médico'}), 500
    finally:
        conn.close()

# Endpoint para crear un nuevo médico
@doctors_bp.route('/api/medicos', methods=['POST'])
def create_medico():
    data = request.json
    required_fields = ['nombre_completo', 'especialidad', 'estado']
    
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Faltan campos requeridos'}), 400
        
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Error de conexión a la base de datos'}), 500
        
    try:
        with conn.cursor() as cursor:
            # Verificar si la tabla tiene la columna fecha_creacion
            cursor.execute("""
                SELECT COLUMN_NAME 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_NAME = 'medicos' AND COLUMN_NAME = 'fecha_creacion'
            """)
            tiene_fecha_creacion = cursor.fetchone()
            
            if tiene_fecha_creacion:
                cursor.execute("""
                    INSERT INTO medicos (
                        nombre_completo, 
                        especialidad, 
                        telefono, 
                        correo, 
                        estado,
                        fecha_creacion
                    ) VALUES (?, ?, ?, ?, ?, GETDATE())
                """, (
                    data['nombre_completo'],
                    data['especialidad'],
                    data.get('telefono'),
                    data.get('correo'),
                    data['estado']
                ))
            else:
                cursor.execute("""
                    INSERT INTO medicos (
                        nombre_completo, 
                        especialidad, 
                        telefono, 
                        correo, 
                        estado
                    ) VALUES (?, ?, ?, ?, ?)
                """, (
                    data['nombre_completo'],
                    data['especialidad'],
                    data.get('telefono'),
                    data.get('correo'),
                    data['estado']
                ))
            
            conn.commit()
            
            # Obtener ID del nuevo médico
            medico_id = cursor.execute("SELECT SCOPE_IDENTITY()").fetchone()[0]
            
            return jsonify({
                'message': 'Médico creado exitosamente',
                'id_medico': medico_id
            }), 201
    except pyodbc.Error as e:
        conn.rollback()
        logging.error(f"Error en base de datos: {str(e)}")
        return jsonify({'error': 'Error al crear médico', 'detalles': str(e)}), 500
    finally:
        conn.close()

@doctors_bp.route('/api/medicos/<int:id_medico>', methods=['PUT'])
def update_medico(id_medico):
    data = request.json
    required_fields = ['nombre_completo', 'especialidad', 'estado']
    
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Faltan campos requeridos'}), 400
        
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Error de conexión a la base de datos'}), 500
        
    try:
        with conn.cursor() as cursor:
            # Verificar si la tabla tiene la columna fecha_actualizacion
            cursor.execute("""
                SELECT COLUMN_NAME 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_NAME = 'medicos' AND COLUMN_NAME = 'fecha_actualizacion'
            """)
            tiene_fecha_actualizacion = cursor.fetchone()
            
            if tiene_fecha_actualizacion:
                cursor.execute("""
                    UPDATE medicos SET
                        nombre_completo = ?,
                        especialidad = ?,
                        telefono = ?,
                        correo = ?,
                        estado = ?,
                        fecha_actualizacion = GETDATE()
                    WHERE id_medico = ?
                """, (
                    data['nombre_completo'],
                    data['especialidad'],
                    data.get('telefono'),
                    data.get('correo'),
                    data['estado'],
                    id_medico
                ))
            else:
                cursor.execute("""
                    UPDATE medicos SET
                        nombre_completo = ?,
                        especialidad = ?,
                        telefono = ?,
                        correo = ?,
                        estado = ?
                    WHERE id_medico = ?
                """, (
                    data['nombre_completo'],
                    data['especialidad'],
                    data.get('telefono'),
                    data.get('correo'),
                    data['estado'],
                    id_medico
                ))
            
            if cursor.rowcount == 0:
                return jsonify({'error': 'Médico no encontrado'}), 404
                
            conn.commit()
            
            return jsonify({'message': 'Médico actualizado exitosamente'})
    except pyodbc.Error as e:
        conn.rollback()
        logging.error(f"Error en base de datos: {str(e)}")
        return jsonify({'error': 'Error al actualizar médico', 'detalles': str(e)}), 500
    finally:
        conn.close()

@doctors_bp.route('/api/medicos/<int:id_medico>', methods=['DELETE'])
def delete_medico(id_medico):
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Error de conexión a la base de datos'}), 500
        
    try:
        with conn.cursor() as cursor:
            # Verificar citas programadas
            cursor.execute("""
                SELECT 1 FROM citas WHERE id_medico = ? AND fecha_cita >= CAST(GETDATE() AS DATE)
            """, (id_medico,))
            
            if cursor.fetchone():
                return jsonify({
                    'error': 'No se puede eliminar el médico porque tiene citas programadas'
                }), 400
                
            # Verificar si la tabla tiene la columna fecha_actualizacion
            cursor.execute("""
                SELECT COLUMN_NAME 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_NAME = 'medicos' AND COLUMN_NAME = 'fecha_actualizacion'
            """)
            tiene_fecha_actualizacion = cursor.fetchone()
            
            if tiene_fecha_actualizacion:
                cursor.execute("""
                    UPDATE medicos SET
                        estado = 'I',
                        fecha_actualizacion = GETDATE()
                    WHERE id_medico = ?
                """, (id_medico,))
            else:
                cursor.execute("""
                    UPDATE medicos SET
                        estado = 'I'
                    WHERE id_medico = ?
                """, (id_medico,))
            
            if cursor.rowcount == 0:
                return jsonify({'error': 'Médico no encontrado'}), 404
                
            conn.commit()
            
            return jsonify({'message': 'Médico marcado como inactivo exitosamente'})
    except pyodbc.Error as e:
        conn.rollback()
        logging.error(f"Error en base de datos: {str(e)}")
        return jsonify({'error': 'Error al eliminar médico', 'detalles': str(e)}), 500
    finally:
        conn.close()