from app import create_app
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)

app = create_app()

if __name__ == '__main__':
    logging.info("Iniciando aplicación Flask...")
    app.run(debug=True, host='0.0.0.0', port=5000)