from flask import Blueprint, request, jsonify
import pyodbc
import logging
import datetime
from database import get_db_connection

appointments_bp = Blueprint('appointments', __name__)

# Endpoint para obtener horarios disponibles de un médico
@appointments_bp.route('/api/medicos/<int:id_medico>/horarios', methods=['GET'])
def get_horarios_disponibles(id_medico):
    fecha = request.args.get('fecha')
    if not fecha:
        return jsonify({'error': 'Fecha no proporcionada'}), 400
        
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Error de conexión a la base de datos'}), 500
        
    try:
        with conn.cursor() as cursor:
            # Obtener horario laboral del médico
            cursor.execute("""
                SELECT hora_inicio, hora_fin 
                FROM horarios_disponibles 
                WHERE id_medico = ? AND dia_semana = DATENAME(WEEKDAY, ?)
            """, (id_medico, fecha))
            
            horario = cursor.fetchone()
            if not horario:
                return jsonify({'error': 'El médico no trabaja ese día'}), 400
                
            hora_inicio = horario[0]
            hora_fin = horario[1]
            
            # Obtener citas existentes para ese médico y fecha
            cursor.execute("""
                SELECT hora_cita 
                FROM citas 
                WHERE id_medico = ? AND fecha_cita = ?
                ORDER BY hora_cita
            """, (id_medico, fecha))
            
            citas_existentes = [row[0] for row in cursor.fetchall()]
            
            # Generar franjas horarias disponibles (cada 30 minutos)
            horarios_disponibles = []
            hora_actual = hora_inicio
            while hora_actual < hora_fin:
                if hora_actual not in citas_existentes:
                    horarios_disponibles.append(hora_actual.strftime('%H:%M'))
                hora_actual = (datetime.datetime.min + (hora_actual - datetime.datetime.min) + datetime.timedelta(minutes=30)).time()
            
            return jsonify(horarios_disponibles)
    except pyodbc.Error as e:
        logging.error(f"Error en base de datos: {str(e)}")
        return jsonify({'error': 'Error al obtener horarios'}), 500
    finally:
        conn.close()

# Endpoint para crear nueva cita
@appointments_bp.route('/api/citas', methods=['POST'])
def crear_cita():
    data = request.json
    required_fields = ['id_medico', 'id_paciente', 'fecha_cita', 'hora_cita', 'motivo_consulta']
    
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Faltan campos requeridos'}), 400
        
    try:
        # Validar que la fecha no sea en el pasado
        fecha_cita = datetime.datetime.strptime(data['fecha_cita'], '%Y-%m-%d').date()
        if fecha_cita < datetime.date.today():
            return jsonify({'error': 'No se pueden programar citas en fechas pasadas'}), 400
            
        # Validar formato de hora
        datetime.datetime.strptime(data['hora_cita'], '%H:%M')
    except ValueError as e:
        return jsonify({'error': 'Formato de fecha u hora inválido'}), 400
        
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Error de conexión a la base de datos'}), 500
        
    try:
        with conn.cursor() as cursor:
            # Verificar disponibilidad del médico
            cursor.execute("""
                SELECT 1 
                FROM citas 
                WHERE id_medico = ? AND fecha_cita = ? AND hora_cita = ?
            """, (data['id_medico'], data['fecha_cita'], data['hora_cita']))
            
            if cursor.fetchone():
                return jsonify({'error': 'El médico ya tiene una cita programada en ese horario'}), 400
                
            # Insertar nueva cita
            cursor.execute("""
                INSERT INTO citas (
                    id_medico, 
                    id_paciente, 
                    fecha_cita, 
                    hora_cita, 
                    motivo_consulta,
                    fecha_creacion
                ) VALUES (?, ?, ?, ?, ?, GETDATE())
            """, (
                data['id_medico'],
                data['id_paciente'],
                data['fecha_cita'],
                data['hora_cita'],
                data['motivo_consulta']
            ))
            
            conn.commit()
            
            # Obtener ID de la nueva cita
            cursor.execute("SELECT SCOPE_IDENTITY()")
            cita_id = cursor.fetchone()[0]
            
            return jsonify({
                'message': 'Cita programada exitosamente',
                'cita_id': cita_id
            }), 201
    except pyodbc.Error as e:
        conn.rollback()
        logging.error(f"Error en base de datos: {str(e)}")
        return jsonify({'error': 'Error al programar la cita'}), 500
    finally:
        conn.close()