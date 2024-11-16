# main.py
import asyncio
from config import logger
from asterisk_manager import AsteriskManager
from telegram_handler import TelegramBot
from event_handler import handle_user_event

async def main_manager(asterisk_manager):
    """Mantener conexión persistente con AMI."""
    try:
        await asterisk_manager.connect()
        asterisk_manager.register_event_handlers(handle_user_event)
        while True:
            await asyncio.sleep(1)
    except Exception as e:
        logger.error(f"Error en la conexión AMI: {e}")
    finally:
        await asterisk_manager.close()

def main():
    """Iniciar bot y conexión AMI."""
    # Inicializar manager de Asterisk
    asterisk_manager = AsteriskManager()
    
    # Inicializar bot de Telegram
    telegram_bot = TelegramBot(asterisk_manager)
    application = telegram_bot.setup()
    
    # Configurar y ejecutar el loop de eventos
    loop = asyncio.get_event_loop()
    loop.create_task(main_manager(asterisk_manager))
    
    # Iniciar el bot
    application.run_polling()

if __name__ == "__main__":
    main()