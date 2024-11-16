# telegram_handler.py
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from config import TELEGRAM_TOKEN, AUTHORIZED_CHAT_IDS, IVR_OPTIONS, user_data
from models import Params

async def send_telegram_message(chat_id: int, message: str):
    """Enviar mensaje a Telegram."""
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    await application.bot.send_message(chat_id=chat_id, text=message)

class TelegramBot:
    def __init__(self, asterisk_manager):
        self.asterisk_manager = asterisk_manager

    async def start_call(self, update, context):
        """Iniciar proceso de llamada."""
        chat_id = update.effective_chat.id
        if chat_id in AUTHORIZED_CHAT_IDS and user_data.get(chat_id, {}).get('step', 'idle') == 'idle':
            await send_telegram_message(chat_id, "📱 Ingresa el número:")
            user_data[chat_id] = {'step': 'phone'}
        else:
            await send_telegram_message(chat_id, "⚠️ Llamada en curso o sin permisos")

    async def hangup(self, update, context):
        """Colgar llamada activa."""
        chat_id = update.effective_chat.id
        channel = user_data.get(chat_id, {}).get('channel')
        if channel:
            await self.asterisk_manager.hangup_call(channel, chat_id)
            user_data[chat_id] = {'step': 'idle'}
        else:
            await send_telegram_message(chat_id, "❌ No hay llamada activa")

    async def handle_message(self, update, context):
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
                await self.asterisk_manager.initiate_call(params, chat_id)
            else:
                await send_telegram_message(chat_id, "⚠️ Opción inválida")

    def setup(self):
        """Configurar manejadores del bot."""
        application = Application.builder().token(TELEGRAM_TOKEN).build()
        application.add_handler(CommandHandler("call", self.start_call))
        application.add_handler(CommandHandler("hangup", self.hangup))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        return application