import asyncio
import logging
from panoramisk import Manager
from pydantic import BaseModel
from telegram.ext import Application, CommandHandler, MessageHandler, filters

# Configuración del bot de Telegram
TELEGRAM_TOKEN = "7785556123:AAGOnrh2UshZOwAICaqc1hd_wEt04uKWW-g"
AUTHORIZED_CHAT_IDS = [428655938]  # Chat ID autorizado

# Configuración de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Opciones del IVR con descripción amigable y contexto técnico
IVR_OPTIONS = {
    "1": {"context": "bank_credit", "description": "Banco 🏦"},
    "2": {"context": "customer_service", "description": "Cliente 📞"},
    "3": {"context": "sales", "description": "Ventas 🛒"},
}

# Almacén temporal de datos del usuario
user_data = {}

# Manager global para la conexión al AMI
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
    """Iniciar una llamada."""
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
        message = f"Llamada iniciada: {response.get('Message')}"
        logger.info(message)
        await send_telegram_message(chat_id, message)
    except Exception as e:
        logger.error(f"Error iniciando llamada: {e}")
        await send_telegram_message(chat_id, "Error al iniciar la llamada.")


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
        logger.error(f"Error al colgar llamada: {e}")
        await send_telegram_message(chat_id, "Error al colgar la llamada.")


async def handle_user_event(manager, event):
    """Manejar eventos de llamadas."""
    event_type = event.Event
    channel = event.get('Channel')

    if event_type == 'Hangup':
        logger.info(f"Llamada colgada: {channel}")
        for chat_id in AUTHORIZED_CHAT_IDS:
            user_data[chat_id] = {'step': 'idle'}
            user_data[chat_id].pop('channel', None)
            await send_telegram_message(chat_id, "Llamada finalizada.")


# ====== CICLO PRINCIPAL DEL MANAGER ======

async def main_manager():
    """Mantener la conexión al AMI."""
    try:
        await manager.connect()
        logger.info("Conexión AMI establecida.")

        manager.register_event('Hangup', lambda m, e: asyncio.create_task(handle_user_event(m, e)))

        while True:
            await asyncio.sleep(1)
    except Exception as e:
        logger.error(f"Error en AMI: {e}")
    finally:
        await manager.close()
        logger.info("Conexión AMI cerrada.")


# ====== FUNCIONES DEL BOT ======

async def start_call(update, context):
    """Iniciar llamada desde Telegram."""
    chat_id = update.effective_chat.id
    if chat_id in AUTHORIZED_CHAT_IDS and user_data.get(chat_id, {}).get('step', 'idle') == 'idle':
        await send_telegram_message(chat_id, "Ingresa el número de teléfono:")
        user_data[chat_id] = {'step': 'phone'}
    else:
        await send_telegram_message(chat_id, "Ya tienes una llamada activa o no tienes permisos.")


async def hangup(update, context):
    """Colgar llamada activa desde Telegram."""
    chat_id = update.effective_chat.id
    channel = user_data.get(chat_id, {}).get('channel')
    if channel:
        await hangup_call(channel, chat_id)
        user_data[chat_id] = {'step': 'idle'}
    else:
        await send_telegram_message(chat_id, "No hay llamadas activas.")


async def handle_message(update, context):
    """Procesar mensajes del usuario."""
    chat_id = update.effective_chat.id
    if chat_id not in user_data:
        await send_telegram_message(chat_id, "Usa /call para iniciar.")
        return

    step = user_data[chat_id].get('step')
    if step == 'phone':
        phone_number = update.message.text.strip()
        channel = f'PJSIP/{phone_number}' if len(phone_number) < 5 else f'PJSIP/{phone_number}@callwithus'
        user_data[chat_id]['channel'] = channel
        user_data[chat_id]['step'] = 'ivr'
        options_text = "Elige una opción:\n" + "\n".join(
            [f"{key}. {value['description']}" for key, value in IVR_OPTIONS.items()]
        )
        await send_telegram_message(chat_id, options_text)
    elif step == 'ivr':
        ivr_choice = update.message.text.strip()
        if ivr_choice in IVR_OPTIONS:
            ivr_context = IVR_OPTIONS[ivr_choice]["context"]
            params = Params(channel=user_data[chat_id]['channel'], ivr=ivr_context)
            await send_telegram_message(chat_id, f"Llamando a {IVR_OPTIONS[ivr_choice]['description']}...")
            await initiate_call(params, chat_id)
        else:
            await send_telegram_message(chat_id, "Opción inválida.")


# ====== CONFIGURAR Y EJECUTAR EL BOT ======

def setup_bot():
    """Configurar el bot."""
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    application.add_handler(CommandHandler("call", start_call))
    application.add_handler(CommandHandler("hangup", hangup))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    return application


def main():
    """Iniciar el bot y AMI."""
    application = setup_bot()
    loop = asyncio.get_event_loop()
    loop.create_task(main_manager())
    application.run_polling()


if __name__ == "__main__":
    main()
