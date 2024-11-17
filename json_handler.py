import aiofiles
from pathlib import Path
import json

# Ruta del archivo JSON
AUTHORIZED_CHAT_IDS_FILE = Path("authorized_chat_ids.json")

async def get_chats_ids():
    """
    Carga los chat_id autorizados desde el archivo JSON.
    Si el archivo no existe, retorna un array vacío.
    """
    if not AUTHORIZED_CHAT_IDS_FILE.exists():
        return []  # Si el archivo no existe, retorna un array vacío.

    async with aiofiles.open(AUTHORIZED_CHAT_IDS_FILE, 'r') as file:
        try:
            content = await file.read()
            return json.loads(content)
        except json.JSONDecodeError:
            # Si el archivo está vacío o mal formado, retorna un array vacío.
            return []

async def save_chat_ids(chat_ids):
    """
    Guarda los chat_id en el archivo JSON.
    """
    async with aiofiles.open(AUTHORIZED_CHAT_IDS_FILE, 'w') as file:
        await file.write(json.dumps(chat_ids))
