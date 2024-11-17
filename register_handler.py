from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ConversationHandler, CommandHandler, MessageHandler, filters, CallbackContext
from json_handler import get_chats_ids, save_chat_ids

# Estados de la conversación
ASK_PASSWORD = 0

# Variable para almacenar temporalmente los usuarios en proceso de registro
pending_registration = {}

async def start_register(update: Update, context: CallbackContext):
    """
    Inicia el proceso de registro de chat_id.
    """
    chat_id = update.effective_chat.id
    AUTHORIZED_CHAT_IDS = await get_chats_ids()

    # Si el usuario ya está autorizado
    if chat_id in AUTHORIZED_CHAT_IDS:
        await update.message.reply_text("✅ Ya estás registrado.")
        return ConversationHandler.END

    # Iniciar el proceso de registro
    pending_registration[chat_id] = True
    await update.message.reply_text("🔑 Ingresa el password para registrarte:")
    return ASK_PASSWORD

async def verify_password(update: Update, context: CallbackContext):
    """
    Verifica el password proporcionado y registra el chat_id si es válido.
    """
    chat_id = update.effective_chat.id
    password = update.message.text.strip()

    # Verificar el password
    REGISTER_PASSWORD = "Mja88848484@#$"
    if password == REGISTER_PASSWORD:
        # Registrar chat_id
        chat_ids = await get_chats_ids()
        if chat_id not in chat_ids:
            chat_ids.append(chat_id)
            await save_chat_ids(chat_ids)

        await update.message.reply_text("✅ Registro exitoso. Ya puedes usar los comandos disponibles.")
        return ConversationHandler.END

    # Password incorrecto
    await update.message.reply_text("❌ Password incorrecto. Inténtalo de nuevo:")
    return ASK_PASSWORD

async def cancel_registration(update: Update, context: CallbackContext):
    """
    Cancela el proceso de registro.
    """
    await update.message.reply_text("❌ Registro cancelado.")
    return ConversationHandler.END

def get_registration_handler():
    """
    Devuelve un ConversationHandler configurado para manejar el registro.
    """
    return ConversationHandler(
        entry_points=[CommandHandler("register", start_register)],
        states={
            ASK_PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, verify_password)],
        },
        fallbacks=[CommandHandler("cancel", cancel_registration)],
    )
