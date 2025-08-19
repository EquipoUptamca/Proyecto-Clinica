from flask import Blueprint, jsonify
import pyodbc
import logging
from database import get_db_connection

dashboard_bp = Blueprint('dashboard', __name__)

# API para obtener datos del dashboard de administrador
@dashboard_bp.route('/api/admin/stats', methods=['GET'])
def admin_stats():
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
        
    cursor = None
    try:
        cursor = conn.cursor()
        
        stats = {}
        
        # Obtener conteo de médicos
        cursor.execute("SELECT COUNT(*) FROM medicos WHERE estado = 'A'")
        stats['doctors'] = cursor.fetchone()[0]
        
        # Obtener conteo de pacientes
        cursor.execute("SELECT COUNT(*) FROM pacientes")
        stats['patients'] = cursor.fetchone()[0]
        
        # Obtener citas para hoy
        cursor.execute("""
            SELECT COUNT(*) 
            FROM citas 
            WHERE CONVERT(date, fecha_cita) = CONVERT(date, GETDATE())
        """)
        stats['appointments'] = cursor.fetchone()[0]
        
        # Obtener conteo de usuarios
        cursor.execute("SELECT COUNT(*) FROM usuarios")
        stats['users'] = cursor.fetchone()[0]
        
        return jsonify(stats)
    except pyodbc.Error as e:
        logging.error(f"Database error in admin_stats: {str(e)}")
        return jsonify({'error': 'Failed to fetch stats'}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

# API para obtener registros recientes
@dashboard_bp.route('/api/admin/recent-activity', methods=['GET'])
def recent_activity():
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
        
    cursor = None
    try:
        cursor = conn.cursor()
        
        # Obtener últimos 5 médicos registrados
        cursor.execute("""
            SELECT TOP 5 id_medico, nombre_completo, especialidad, 
                   CONVERT(varchar, GETDATE(), 120) as fecha
            FROM medicos
            ORDER BY id_medico DESC
        """)
        doctors = [{
            'id': row[0],
            'name': row[1],
            'type': 'Médico',
            'specialty': row[2],
            'date': row[3]
        } for row in cursor.fetchall()]
        
        # Obtener últimos 5 pacientes registrados
        cursor.execute("""
            SELECT TOP 5 id_paciente, nombre_completo, 
                   CONVERT(varchar, GETDATE(), 120) as fecha
            FROM pacientes
            ORDER BY id_paciente DESC
        """)
        patients = [{
            'id': row[0],
            'name': row[1],
            'type': 'Paciente',
            'date': row[2]
        } for row in cursor.fetchall()]
        
        # Obtener últimas 5 citas programadas
        cursor.execute("""
            SELECT TOP 5 c.id_cita, p.nombre_completo, m.nombre_completo,
                   CONVERT(varchar, c.fecha_cita, 120) + ' ' + CONVERT(varchar, c.hora_cita, 108) as fecha
            FROM citas c
            JOIN pacientes p ON c.id_paciente = p.id_paciente
            JOIN medicos m ON c.id_medico = m.id_medico
            ORDER BY c.fecha_cita DESC, c.hora_cita DESC
        """)
        appointments = [{
            'id': row[0],
            'name': f"Cita {row[0]}",
            'type': 'Cita',
            'details': f"Paciente: {row[1]}, Médico: {row[2]}",
            'date': row[3]
        } for row in cursor.fetchall()]
        
        # Combinar todos los resultados y ordenar por fecha
        recent_activity = doctors + patients + appointments
        recent_activity.sort(key=lambda x: x['date'], reverse=True)
        
        return jsonify(recent_activity[:10])  # Devolver solo los 10 más recientes
    except pyodbc.Error as e:
        logging.error(f"Database error in recent_activity: {str(e)}")
        return jsonify({'error': 'Failed to fetch recent activity'}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

# API para obtener datos del usuario actual
@dashboard_bp.route('/api/user-data', methods=['GET'])
def user_data():
    # En una aplicación real, esto vendría de la sesión o token JWT
    # Aquí es un ejemplo simplificado
    return jsonify({
        'nombre': 'Administrador Principal',
        'rol': 'Administrador'
    })