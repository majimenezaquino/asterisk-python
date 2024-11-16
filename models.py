# models.py
from pydantic import BaseModel

class Params(BaseModel):
    channel: str
    ivr: str