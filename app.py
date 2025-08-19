from flask import Flask
import logging

# Import blueprints
from views import views_bp
from auth import auth_bp
from dashboard import dashboard_bp
from users import users_bp
from doctors import doctors_bp
from patients import patients_bp
from appointments import appointments_bp
from schedules import schedules_bp

def create_app():
    app = Flask(__name__, template_folder='templates', static_folder='static')
    
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Register blueprints
    app.register_blueprint(views_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(doctors_bp)
    app.register_blueprint(patients_bp)
    app.register_blueprint(appointments_bp)
    app.register_blueprint(schedules_bp)
    
    return app