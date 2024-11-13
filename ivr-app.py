import asyncio
import logging
from panoramisk import Manager
from datetime import datetime

# Configuración de logging para ver los eventos importantes en detalle
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Variable global para el estado del PIN
pin_validated = False

def log_pin_attempt(channel, pin, result):
    """Función para registrar el intento de PIN en un archivo de texto"""
    date_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    called_number = channel.split('/')[-1]  # Extraer número del canal, si está en el formato `PJSIP/numero`
    with open("pin_attempts.txt", "a") as file:
        file.write(f"Fecha: {date_time}, Número llamado: {called_number}, PIN ingresado: {pin}, Resultado: {result}\n")

async def validate_pin(manager, pin, channel):
    global pin_validated
    expected_pin = "123456999999"  # Cambia esto para obtener el PIN esperado desde una base de datos si es necesario
    
    logger.info(f"=== Validación de PIN ===")
    logger.info(f"PIN recibido: '{pin}'")
    logger.info(f"PIN esperado: '{expected_pin}'")
    logger.info(f"Canal: {channel}")
    
    # Comparación del PIN
    if pin == expected_pin:
        pin_validated = True
        result = "valid"
        logger.info("Resultado: PIN VÁLIDO ✓")
    else:
        pin_validated = False
        result = "invalid"
        logger.info("Resultado: PIN INVÁLIDO ✗")

    # Registrar el intento de PIN en el archivo de texto
    log_pin_attempt(channel, pin, result)

    # Configurar variable de estado en Asterisk
    set_var_action = {
        'Action': 'SetVar',
        'Channel': channel,
        'Variable': 'pin_status',
        'Value': result
    }
    
    try:
        response = await manager.send_action(set_var_action)
        message = response.get('Message')
        logger.info(f"Respuesta de Asterisk: {message}")
    except Exception as e:
        logger.error(f"Error al configurar variable: {e}")

async def handle_user_event(manager, event):
    """Manejar eventos específicos relacionados al PIN"""
    global pin_validated
    if event.Event == 'VarSet':
        if event.Variable == 'pin':
            pin = event.Value
            channel = event.Channel
            await validate_pin(manager, pin, channel)
        elif event.Variable == 'READSTATUS' and event.Value == 'TIMEOUT' and not pin_validated:
            pass

async def initiate_call(manager):
    """Función para iniciar la llamada"""
    originate_action = {
        'Action': 'Originate',
        'Channel': 'PJSIP/573212262637@signalwire',  # Cambia el canal a la extensión que desees
        'Context': 'bank_credit',  # Contexto que maneja el IVR en Asterisk
        'Exten': 's',              # Extensión para iniciar el IVR
        'Priority': 1,
        'CallerID': '1002',        # ID de la llamada
        'Timeout': 30000,
        'Async': 'false'
    }
    
    try:
        response = await manager.send_action(originate_action)
        message = response.get('Message')
        logger.info(f"Respuesta de inicio de llamada: {message}")
    except Exception as e:
        logger.error(f"Error al iniciar llamada: {e}")

async def handle_events(manager, event):
    logger.info(f"Evento recibido custom: {event}")

async def handle_ivr_status(manager, event):
    """Manejar eventos de IVR personalizados de Asterisk"""
    step = event.get('AppData')
    
    if step:
        logger.info(f"IVR Step: {step}")

async def main():
    # Conectarse al AMI de Asterisk
    manager = Manager(
        host='localhost',
        port=5038,
        username='python_user',
        secret='admin'
    )
    
    try:
        await manager.connect()
        logger.info("Conectado a Asterisk AMI")
        # Registrar el evento específico para manejo del PIN
        manager.register_event('VarSet', handle_user_event)
        manager.register_event('*', handle_ivr_status) 
        
        # Iniciar la llamada
        await initiate_call(manager)
        
        # Mantener el script corriendo para escuchar los eventos en tiempo real
        while True:
            await asyncio.sleep(1)
            
    except Exception as e:
        logger.error(f"Error en el loop principal: {e}", exc_info=True)
    finally:
        await manager.close()
        logger.info("Conexión AMI cerrada")

if __name__ == "__main__":
    asyncio.run(main())
