# config.py
import logging

# Configuración del bot
# TELEGRAM_TOKEN = "7785556123:AAGOnrh2UshZOwAICaqc1hd_wEt04uKWW-g"
TELEGRAM_TOKEN = "7753900446:AAG2Ib3XOYIruTl4Cnq76ENLH69N8WZ7af8"

# Configuración de Asterisk
ASTERISK_CONFIG = {
    "host": "localhost",
    "port": 5038,
    "username": "python_user",
    "secret": "admin",
}

# Opciones de IVR
IVR_OPTIONS = {
    "1": {"context": "banco", "description": "🇪🇸 CC Llamada Sin Representante"},
    "2": {"context": "banco_ex", "description": "🇪🇸 CC Llamada Con Representante"},
    "3": {"context": "bank", "description": "🇬🇧 CC Call Without Representative"},
    "4": {"context": "bank_ex", "description": "🇬🇧 CC Call With Representative"},
}

# Configuración de logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Diccionario global para datos de usuario
user_data = {}
