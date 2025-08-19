import os

# Database configuration
SERVER = os.getenv('DB_SERVER', r'localhost\SQLEXPRESS')  # Raw string for backslash
DATABASE = os.getenv('DB_DATABASE', 'asistencia_medica_clinica')
USE_WINDOWS_AUTH = os.getenv('USE_WINDOWS_AUTH', 'True').lower() == 'true'

# Only use these if Windows Auth is False
USERNAME = os.getenv('DB_USERNAME', r'RAFA2004\YepBuddy2')  # Raw string
PASSWORD = os.getenv('DB_PASSWORD', 'your_secure_password')  # Never leave empty

# Diccionario de nombres de días
DAY_NAMES = {
    1: 'Lunes',
    2: 'Martes',
    3: 'Miércoles',
    4: 'Jueves',
    5: 'Viernes',
    6: 'Sábado',
    7: 'Domingo'
}