from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ConversationHandler, CommandHandler, MessageHandler, CallbackQueryHandler, filters, CallbackContext
from audio_handler import create_personalized_audio, PersonalData

# Estados de la conversación
ASK_LANGUAGE, ASK_SEX, ASK_NAME, ASK_BANK, ASK_CARD_TYPE, ASK_CREDIT_CARD, ASK_REPRESENTATIVE = range(7)

# Variables para almacenar los datos temporalmente
user_data = {}

async def start_convert_audio(update: Update, context: CallbackContext):
    """Inicia el proceso de recopilación de datos."""
    user_data.clear()  # Limpia los datos previos

    # Teclado para seleccionar idioma
    keyboard = [
        [InlineKeyboardButton("🇪🇸 Español", callback_data='es')],
        [InlineKeyboardButton("🇬🇧 English", callback_data='en')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Elige idioma:" if context.user_data.get('language') == 'es' else "Choose a language:",
        reply_markup=reply_markup,
    )
    return ASK_LANGUAGE

async def ask_sex(update: Update, context: CallbackContext):
    """Pregunta el sexo."""
    query = update.callback_query
    await query.answer()
    user_data['language'] = query.data

    # Teclado para seleccionar sexo
    keyboard = [
        [InlineKeyboardButton("👨 Hombre", callback_data='M')],
        [InlineKeyboardButton("👩 Mujer", callback_data='F')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(
        "Selecciona el género:" if user_data['language'] == 'es' else "Select gender:",
        reply_markup=reply_markup,
    )
    return ASK_SEX

async def ask_name(update: Update, context: CallbackContext):
    """Pregunta el nombre."""
    query = update.callback_query
    await query.answer()
    user_data['sex'] = query.data

    await query.message.reply_text(
        "Nombre completo:" if user_data['language'] == 'es' else "Full name:"
    )
    return ASK_NAME

async def ask_bank(update: Update, context: CallbackContext):
    """Pregunta el nombre del banco."""
    user_data['name'] = update.message.text.strip()

    await update.message.reply_text(
        "Banco asociado:" if user_data['language'] == 'es' else "Bank name:"
    )
    return ASK_BANK

async def ask_card_type(update: Update, context: CallbackContext):
    """Pregunta el tipo de tarjeta."""
    user_data['bank_name'] = update.message.text.strip()

    await update.message.reply_text(
        "Tipo de tarjeta (Visa, MasterCard):" if user_data['language'] == 'es' else "Card type (Visa, MasterCard):"
    )
    return ASK_CARD_TYPE

async def ask_credit_card(update: Update, context: CallbackContext):
    """Pregunta los últimos 4 dígitos de la tarjeta."""
    user_data['card_type'] = update.message.text.strip()

    await update.message.reply_text(
        "Últimos 4 dígitos:" if user_data['language'] == 'es' else "Last 4 digits:"
    )
    return ASK_CREDIT_CARD

async def ask_representative(update: Update, context: CallbackContext):
    """Pregunta si hay un representante."""
    user_data['credit_card'] = update.message.text.strip()

    # Teclado para seleccionar si hay representante
    keyboard = [
        [InlineKeyboardButton("✅ Sí", callback_data='True')],
        [InlineKeyboardButton("❌ No", callback_data='False')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Habilitar la transferencia a un representante." if user_data['language'] == 'es' else "Do you have an authorized representative?",
        reply_markup=reply_markup,
    )
    return ASK_REPRESENTATIVE

async def generate_audio_and_send(update: Update, context: CallbackContext):
    """Genera el audio con los datos proporcionados y lo envía al usuario."""
    query = update.callback_query
    await query.answer()
    user_data['has_representation'] = query.data == 'True'  # Convertir a booleano

    try:
          # Indicar al usuario que espere
        lang = user_data.get('language', 'es')
        await query.message.reply_text(
            "Generando audio, por favor espere..." if lang == 'es' else "Generating audio, please wait..."
        )
        # Crear objeto `PersonalData` con los datos actuales
        data = PersonalData(
            sex=user_data['sex'],
            name=user_data['name'],
            bank_name=user_data['bank_name'],
            credit_card=user_data['card_type'],
            last_code=user_data['credit_card'],
            has_representation=user_data['has_representation']  # Nuevo campo
        )

        lang = user_data.get('language', 'es')

        # Generar audio
        audio_file = create_personalized_audio(data, lang)

        # Enviar audio
        await query.message.reply_text(
            "Audio listo. Enviando..." if lang == 'es' else "Audio ready. Sending..."
        )

        with open(audio_file, 'rb') as audio:
            await context.bot.send_audio(chat_id=update.effective_chat.id, audio=audio)

    except Exception as e:
        await query.message.reply_text(
            f"Error: {e}" if user_data['language'] == 'es' else f"Error: {e}"
        )

    return ConversationHandler.END

async def cancel(update: Update, context: CallbackContext):
    """Cancela la conversación."""
    await update.message.reply_text(
        "Operación cancelada." if user_data.get('language') == 'es' else "Operation canceled."
    )
    return ConversationHandler.END

def get_conversation_handler():
    """Devuelve un ConversationHandler configurado."""
    return ConversationHandler(
        entry_points=[CommandHandler("generate", start_convert_audio)],
        states={
            ASK_LANGUAGE: [CallbackQueryHandler(ask_sex)],
            ASK_SEX: [CallbackQueryHandler(ask_name)],
            ASK_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_bank)],
            ASK_BANK: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_card_type)],
            ASK_CARD_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_credit_card)],
            ASK_CREDIT_CARD: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_representative)],
            ASK_REPRESENTATIVE: [CallbackQueryHandler(generate_audio_and_send)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
