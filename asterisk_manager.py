# asterisk_manager.py
import asyncio
from panoramisk import Manager
from config import ASTERISK_CONFIG, logger
from telegram_handler import send_telegram_message
from models import Params

class AsteriskManager:
    def __init__(self):
        self.manager = Manager(
            host=ASTERISK_CONFIG['host'],
            port=ASTERISK_CONFIG['port'],
            username=ASTERISK_CONFIG['username'],
            secret=ASTERISK_CONFIG['secret']
        )

    async def connect(self):
        """Establecer conexión con Asterisk AMI."""
        await self.manager.connect()
        logger.info("Conexión establecida con Asterisk AMI.")

    async def close(self):
        """Cerrar conexión con Asterisk AMI."""
        await self.manager.close()
        logger.info("Conexión cerrada con Asterisk AMI.")

    async def initiate_call(self, params: Params, chat_id: int, caller_id: str):
        """Iniciar una llamada."""
        originate_action = {
            'Action': 'Originate',
            'Channel': params.channel,
            'Context': params.ivr,
            'Exten': 's',
            'Priority': 1,
            'CallerID': f'<{caller_id}>',  # Establece el Caller ID usando el parámetro
            'Timeout': 30000,
            'Async': 'false',
        }
        try:
            response = await self.manager.send_action(originate_action)
            message = f"✅ Llamada iniciada"
            logger.info(message)
            await send_telegram_message(chat_id, message)
        except Exception as e:
            error_message = f"❌ Error: {e}"
            logger.error(error_message)
            await send_telegram_message(chat_id, error_message)

    async def hangup_call(self, channel: str, chat_id: int):
        """Colgar una llamada activa."""
        hangup_action = {
            'Action': 'Hangup',
            'Channel': channel,
        }
        try:
            response = await self.manager.send_action(hangup_action)
            message = f"📴 Llamada finalizada"
            logger.info(message)
            await send_telegram_message(chat_id, message)
        except Exception as e:
            error_message = f"❌ Error al colgar: {e}"
            logger.error(error_message)
            await send_telegram_message(chat_id, error_message)

    def register_event_handlers(self, event_handler):
        """Registrar manejadores de eventos."""
        self.manager.register_event('OriginateResponse', 
            lambda m, e: asyncio.create_task(event_handler(m, e)))
        self.manager.register_event('Newstate', 
            lambda m, e: asyncio.create_task(event_handler(m, e)))
        self.manager.register_event('VarSet', 
            lambda m, e: asyncio.create_task(event_handler(m, e)))
        self.manager.register_event('Hangup', 
            lambda m, e: asyncio.create_task(event_handler(m, e)))
        self.manager.register_event('Newexten', 
            lambda m, e: asyncio.create_task(event_handler(m, e)))