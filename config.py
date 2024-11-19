# config.py
import logging

# Configuración del bot
#TELEGRAM_TOKEN = "7785556123:AAGOnrh2UshZOwAICaqc1hd_wEt04uKWW-g"
TELEGRAM_TOKEN = "7715172117:AAFiYAXJvGH3DzKDJ-iaqruW_44wyWLi0Rw"

# Configuración de Asterisk
ASTERISK_CONFIG = {
    'host': 'localhost',
    'port': 5038,
    'username': 'python_user',
    'secret': 'admin'
}

# Opciones de IVR
IVR_OPTIONS = {
    "1": {"context": "banco", "description": "Tarjeta De Credito ES 🏦"},
    "2": {"context": "bank_credit", "description": "Credit Card EN 🏦"},
    "3": {"context": "sales", "description": "Ventas 🛒"},
}

# Configuración de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Diccionario global para datos de usuario
user_data = {}