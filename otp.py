import asyncio
import logging
from panoramisk import Manager
from datetime import datetime
from pydantic import BaseModel
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Configuración del bot de Telegram
TELEGRAM_TOKEN = "7785556123:AAGOnrh2UshZOwAICaqc1hd_wEt04uKWW-g"
AUTHORIZED_CHAT_IDS = [428655938]  # Chat ID autorizado para recibir eventos

# Configuración de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class Params(BaseModel):
    channel: str
    ivr: str

# Diccionario para manejar datos temporales del usuario
user_data = {}

# Opciones de IVR
IVR_OPTIONS = {
    "1": "banco",
    "2": "servicio_cliente",
    "3": "ventas",
}

async def send_telegram_event(context: ContextTypes.DEFAULT_TYPE, message: str, chat_id: int):
    """Enviar un mensaje a Telegram."""
    if context:
        await context.bot.send_message(chat_id=chat_id, text=message)

async def handle_user_event(manager, event, context=None):
    """Manejar eventos específicos relacionados con el usuario."""
    if event.Event == 'VarSet':
        variable = event.get('Variable')
        value = event.get('Value')
        channel = event.get('Channel')
        event_info = f"Evento: VarSet\nVariable: {variable}\nValor: {value}\nCanal: {channel}"
        logger.info(event_info)

        # Enviar el evento a todos los chats autorizados
        for chat_id in AUTHORIZED_CHAT_IDS:
            if context:
                await send_telegram_event(context, event_info, chat_id)

async def initiate_call(manager, params, context, chat_id):
    """Iniciar la llamada."""
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
        await send_telegram_event(context, message, chat_id)
    except Exception as e:
        error_message = f"Error al iniciar llamada: {e}"
        logger.error(error_message)
        await send_telegram_event(context, error_message, chat_id)

async def main(params, context, chat_id):
    """Conectar al AMI de Asterisk y manejar eventos."""
    manager = Manager(
        host='localhost',
        port=5038,
        username='python_user',
        secret='admin'
    )
    try:
        await manager.connect()
        logger.info("Conectado a Asterisk AMI")

        # Registrar eventos de Asterisk
        manager.register_event('VarSet', lambda m, e: asyncio.create_task(handle_user_event(m, e, context)))

        # Iniciar la llamada
        await initiate_call(manager, params, context, chat_id)

        # Mantener el script escuchando eventos
        while True:
            await asyncio.sleep(1)
    except Exception as e:
        logger.error(f"Error en el loop principal: {e}", exc_info=True)
    finally:
        await manager.close()
        logger.info("Conexión AMI cerrada")

async def start_call(update, context):
    """Iniciar el proceso de llamada."""
    chat_id = update.effective_chat.id
    if chat_id in AUTHORIZED_CHAT_IDS:
        await send_telegram_event(context, "Por favor, ingresa el número de teléfono:", chat_id)
        user_data[chat_id] = {'step': 'phone'}
    else:
        await send_telegram_event(context, "No tienes permisos para iniciar una llamada.", chat_id)

async def handle_message(update, context):
    """Procesar mensajes del usuario."""
    chat_id = update.effective_chat.id
    if chat_id not in user_data:
        await send_telegram_event(context, "Por favor, usa /iniciar_llamada para comenzar.", chat_id)
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
        await send_telegram_event(context, ivr_options_text, chat_id)
    elif step == 'ivr':
        ivr_choice = update.message.text.strip()
        if ivr_choice in IVR_OPTIONS:
            ivr_context = IVR_OPTIONS[ivr_choice]
            channel = user_data[chat_id]['channel']
            params = Params(channel=channel, ivr=ivr_context)
            await send_telegram_event(context, f"Iniciando llamada al canal {channel} en el contexto {ivr_context}...", chat_id)
            await main(params, context, chat_id)
            user_data.pop(chat_id, None)
        else:
            await send_telegram_event(context, "Opción inválida. Selecciona un contexto válido.", chat_id)

def setup_bot():
    """Configurar y ejecutar el bot de Telegram."""
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    application.add_handler(CommandHandler("iniciar_llamada", start_call))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    application.run_polling()

if __name__ == "__main__":
    setup_bot()
