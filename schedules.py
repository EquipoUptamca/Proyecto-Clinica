from flask import Blueprint, request, jsonify, Response
import pyodbc
import logging
from datetime import datetime, timedelta
from database import get_db_connection
from utils import validate_schedule_input, check_schedule_conflict
def check_schedule_conflict(id_medico, dia_semana, hora_inicio, hora_fin, exclude_id=None):
    """Verifica si hay conflictos de horario para el médico"""
    conn = get_db_connection()
    if not conn:
        raise Exception("No se pudo conectar a la base de datos")

    try:
        with conn.cursor() as cursor:
            query = """
                SELECT id_horario
                FROM horarios_disponibles
                WHERE id_medico = ?
                AND dia_semana = ?
                AND (
                    (hora_inicio < ? AND hora_fin > ?)
                    OR (hora_inicio >= ? AND hora_inicio < ?)
                    OR (hora_fin > ? AND hora_fin <= ?)
                )
            """
            params = [id_medico, dia_semana, hora_fin, hora_inicio,
                     hora_inicio, hora_fin, hora_inicio, hora_fin]

            if exclude_id:
                query += " AND id_horario != ?"
                params.append(exclude_id)

            cursor.execute(query, params)
            conflict = cursor.fetchone()
            return conflict is not None

    except pyodbc.Error as e:
        logging.error(f"Error al verificar conflicto de horario: {str(e)}")
        raise
    finally:
        conn.close()
schedules_bp = Blueprint('schedules', __name__)

DAY_NAMES = {
    1: 'Lunes',
    2: 'Martes',
    3: 'Miércoles',
    4: 'Jueves',
    5: 'Viernes',
    6: 'Sábado',
    7: 'Domingo'
}

def validate_day_of_week(day):
    """Validate that day is an integer between 1-7"""
    if not isinstance(day, int):
        try:
            day = int(day)
        except (ValueError, TypeError):
            return False
    return 1 <= day <= 7

@schedules_bp.route('/api/horarios/<int:doctor_id>', methods=['GET'])
def get_doctor_schedules(doctor_id):
    """Obtiene todos los horarios de un médico específico"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Error de conexión a la base de datos'}), 500

    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT id_horario, id_medico, dia_semana, hora_inicio, hora_fin
                FROM horarios_disponibles
                WHERE id_medico = ?
                ORDER BY dia_semana, hora_inicio
            """, (doctor_id,))

            schedules = []
            for row in cursor.fetchall():
                day_num = row[2]
                if not validate_day_of_week(day_num):
                    continue
                day_str = DAY_NAMES.get(day_num, 'Desconocido')
                schedules.append({
                    'id_horario': row[0],
                    'id_medico': row[1],
                    'dia_semana_num': day_num,
                    'dia_semana': day_str,
                    'hora_inicio': str(row[3]),
                    'hora_fin': str(row[4])
                })

            return jsonify(schedules)

    except pyodbc.Error as e:
        logging.error(f"Error al obtener horarios: {str(e)}")
        return jsonify({'error': 'Error al obtener horarios'}), 500
    finally:
        conn.close()

@schedules_bp.route('/api/horarios', methods=['POST'])
def create_schedule():
    """Crea un nuevo horario para un médico"""
    data = request.json
    required_fields = ['id_medico', 'dia_semana', 'hora_inicio', 'hora_fin']

    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Faltan campos requeridos'}), 400

    # Ensure dia_semana is an integer
    try:
        dia_semana = int(data['dia_semana'])
    except (ValueError, TypeError):
        return jsonify({
            'error': 'Día de la semana inválido',
            'detalle': 'Debe ser un número entre 1 (Lunes) y 7 (Domingo).',
            'valor_recibido': data['dia_semana']
        }), 400

    if not validate_day_of_week(dia_semana):
        return jsonify({
            'error': 'Día de la semana inválido',
            'detalle': 'Debe ser un número entre 1 (Lunes) y 7 (Domingo).',
            'valor_recibido': dia_semana
        }), 400

    # Validar el resto de los datos
    if not validate_schedule_input(data['id_medico'], dia_semana,
                                 data['hora_inicio'], data['hora_fin']):
        return jsonify({'error': 'Datos de horario inválidos'}), 400

    # Verificar conflictos - now passing validated integer
    if check_schedule_conflict(data['id_medico'], dia_semana,
                             data['hora_inicio'], data['hora_fin']):
        return jsonify({'error': 'Conflicto de horarios detectado'}), 400

    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Error de conexión a la base de datos'}), 500

    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO horarios_disponibles 
                (id_medico, dia_semana, hora_inicio, hora_fin)
                OUTPUT INSERTED.id_horario
                VALUES (?, ?, ?, ?)
            """, (data['id_medico'], dia_semana, data['hora_inicio'], data['hora_fin']))

            schedule_id = cursor.fetchone()[0]
            conn.commit()

            return jsonify({
                'id_horario': schedule_id,
                'message': 'Horario creado exitosamente',
                'dia_semana_num': dia_semana,
                'dia_semana': DAY_NAMES.get(dia_semana, 'Desconocido')
            }), 201

    except pyodbc.Error as e:
        conn.rollback()
        logging.error(f"Error al crear horario: {str(e)}. Datos enviados: {data}")
        return jsonify({'error': 'Error al crear horario en la base de datos', 'detalle': str(e)}), 500
    finally:
        conn.close()

# ... (rest of your routes remain the same, just ensure they use validate_day_of_week)

@schedules_bp.route('/api/horarios/<int:schedule_id>', methods=['PUT'])
def update_schedule(schedule_id):
    """Actualiza un horario existente"""
    if not request.is_json:
        return jsonify({'error': 'Se esperaba contenido tipo JSON'}), 400

    data = request.get_json()
    if not data:
        return jsonify({'error': 'Datos JSON vacíos o inválidos'}), 400

    # Campos requeridos para actualización
    update_fields = ['dia_semana', 'hora_inicio', 'hora_fin']
    if not any(field in data for field in update_fields):
        return jsonify({
            'error': 'Se requiere al menos un campo para actualizar',
            'campos_posibles': update_fields
        }), 400

    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Error de conexión a la base de datos'}), 500

    try:
        with conn.cursor() as cursor:
            # Obtener el horario actual
            cursor.execute("""
                SELECT id_medico, dia_semana, hora_inicio, hora_fin
                FROM horarios_disponibles
                WHERE id_horario = ?
            """, (schedule_id,))
            
            current = cursor.fetchone()
            if not current:
                return jsonify({'error': 'Horario no encontrado'}), 404

            current_doctor_id = current[0]
            current_values = {
                'dia_semana': current[1],
                'hora_inicio': str(current[2]),
                'hora_fin': str(current[3])
            }

            # Preparar valores actualizados
            updated_values = current_values.copy()
            
            try:
                # Actualizar día si se proporcionó
                if 'dia_semana' in data:
                    dia_semana = data['dia_semana']
                    if isinstance(dia_semana, str) and dia_semana.isdigit():
                        updated_values['dia_semana'] = int(dia_semana)
                    elif isinstance(dia_semana, int):
                        updated_values['dia_semana'] = dia_semana
                    else:
                        raise ValueError("El día debe ser un número entre 1-7")

                # Actualizar horas si se proporcionaron
                if 'hora_inicio' in data:
                    updated_values['hora_inicio'] = str(data['hora_inicio'])
                
                if 'hora_fin' in data:
                    updated_values['hora_fin'] = str(data['hora_fin'])

                # Validar día de la semana
                if not validate_day_of_week(updated_values['dia_semana']):
                    raise ValueError("Día de la semana debe ser entre 1 (Lunes) y 7 (Domingo)")

                # Validar formato de horas
                if not all(':' in t for t in [updated_values['hora_inicio'], updated_values['hora_fin']]):
                    raise ValueError("Las horas deben tener formato HH:MM o HH:MM:SS")

            except ValueError as e:
                return jsonify({
                    'error': 'Datos inválidos',
                    'detalle': str(e),
                    'valores_recibidos': {
                        'dia_semana': data.get('dia_semana'),
                        'hora_inicio': data.get('hora_inicio'),
                        'hora_fin': data.get('hora_fin')
                    },
                    'valores_actuales': current_values
                }), 400

            # Validar lógica de horario
            if not validate_schedule_input(
                current_doctor_id,
                updated_values['dia_semana'],
                updated_values['hora_inicio'],
                updated_values['hora_fin']
            ):
                return jsonify({
                    'error': 'Horario inválido',
                    'detalle': 'La hora de inicio debe ser anterior a la hora de fin'
                }), 400

            # Verificar conflictos
            if check_schedule_conflict(
                current_doctor_id,
                updated_values['dia_semana'],
                updated_values['hora_inicio'],
                updated_values['hora_fin'],
                schedule_id
            ):
                return jsonify({
                    'error': 'Conflicto de horario',
                    'detalle': 'El horario se superpone con otro horario existente'
                }), 400

            # Actualizar en la base de datos
            cursor.execute("""
                UPDATE horarios_disponibles
                SET dia_semana = ?, hora_inicio = ?, hora_fin = ?
                WHERE id_horario = ?
            """, (
                updated_values['dia_semana'],
                updated_values['hora_inicio'],
                updated_values['hora_fin'],
                schedule_id
            ))

            conn.commit()

            if cursor.rowcount > 0:
                return jsonify({
                    'message': 'Horario actualizado correctamente',
                    'horario': {
                        'id_horario': schedule_id,
                        'dia_semana': DAY_NAMES.get(updated_values['dia_semana'], 'Desconocido'),
                        'hora_inicio': updated_values['hora_inicio'],
                        'hora_fin': updated_values['hora_fin']
                    }
                })
            return jsonify({'error': 'No se realizaron cambios en el horario'}), 404

    except pyodbc.Error as e:
        conn.rollback()
        logging.error(f"Error al actualizar horario {schedule_id}: {str(e)}")
        return jsonify({
            'error': 'Error de base de datos',
            'detalle': str(e)
        }), 500
    finally:
        conn.close()

@schedules_bp.route('/api/horarios/<int:schedule_id>', methods=['DELETE'])
def delete_schedule(schedule_id):
    """Elimina un horario"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Error de conexión a la base de datos'}), 500

    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                DELETE FROM horarios_disponibles
                WHERE id_horario = ?
            """, (schedule_id,))

            conn.commit()

            if cursor.rowcount > 0:
                return jsonify({'message': 'Horario eliminado correctamente'})
            else:
                return jsonify({'error': 'Horario no encontrado'}), 404

    except pyodbc.Error as e:
        conn.rollback()
        logging.error(f"Error al eliminar horario: {str(e)}")
        return jsonify({'error': 'Error al eliminar horario'}), 500
    finally:
        conn.close()

@schedules_bp.route('/api/horarios/<int:doctor_id>/semanal', methods=['GET'])
def get_weekly_schedule(doctor_id):
    """Obtiene el horario semanal organizado por día"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Error de conexión a la base de datos'}), 500

    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT id_horario, dia_semana, hora_inicio, hora_fin
                FROM horarios_disponibles
                WHERE id_medico = ?
                ORDER BY dia_semana, hora_inicio
            """, (doctor_id,))

            schedules = cursor.fetchall()
            weekly_schedule = {i: [] for i in range(1, 8)}  # Días 1-7

            for schedule in schedules:
                day_num = int(schedule[1])  # Convertir a entero
                if 1 <= day_num <= 7:  # Validar que esté en el rango correcto
                    weekly_schedule[day_num].append({
                        'id_horario': schedule[0],
                        'hora_inicio': str(schedule[2]),
                        'hora_fin': str(schedule[3])
                    })

            return jsonify(weekly_schedule)

    except (pyodbc.Error, ValueError) as e:
        logging.error(f"Error al obtener horario semanal: {str(e)}")
        return jsonify({'error': 'Error al obtener horario semanal'}), 500
    finally:
        conn.close()

@schedules_bp.route('/api/horarios/<int:doctor_id>/slots', methods=['GET'])
def get_available_time_slots(doctor_id):
    """Obtiene slots de tiempo disponibles para un médico en un día específico"""
    day_of_week = request.args.get('dia_semana', type=int)
    duration_minutes = request.args.get('duracion', default=30, type=int)

    if not day_of_week or not 1 <= day_of_week <= 7:
        return jsonify({'error': 'Día de la semana inválido'}), 400

    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Error de conexión a la base de datos'}), 500

    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT hora_inicio, hora_fin
                FROM horarios_disponibles
                WHERE id_medico = ? AND dia_semana = ?
                ORDER BY hora_inicio
            """, (doctor_id, day_of_week))

            schedules = cursor.fetchall()
            available_slots = []

            for schedule in schedules:
                start_time = schedule[0]
                end_time = schedule[1]

                current_time = datetime.combine(datetime.today(), start_time)
                end_datetime = datetime.combine(datetime.today(), end_time)

                while current_time + timedelta(minutes=duration_minutes) <= end_datetime:
                    available_slots.append(current_time.strftime('%H:%M'))
                    current_time += timedelta(minutes=duration_minutes)

            return jsonify(sorted(available_slots))

    except pyodbc.Error as e:
        logging.error(f"Error al obtener slots disponibles: {str(e)}")
        return jsonify({'error': 'Error al obtener slots disponibles'}), 500
    finally:
        conn.close()

