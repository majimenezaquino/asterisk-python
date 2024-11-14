import asyncio
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from gtts import gTTS
from pydub import AudioSegment
from ivr import main
import os

# Configuration
AUDIO_PATH = "./audios/"

# FastAPI configuration
app = FastAPI(
    title="Custom Audio Message Generation API",
    description="API to convert a custom message into a WAV audio format compatible with Asterisk",
    version="1.0.0"
)
class CallParams(BaseModel):
    channel: str = Field(..., description="Channel to make the call.")
    ivr: str = Field(..., description="IVR context to handle the call.")
# Personal data model
class PersonalData(BaseModel):
    sex: str = Field(..., description="Gender of the person ('M' for male, 'F' for female).")
    name: str = Field(..., description="Name of the person.")
    bank_name: str = Field(..., description="Name of the bank.")
    credit_card: str = Field(..., description="Type of credit card.")
    last_code: str = Field(..., min_length=4, max_length=4, description="Last 4 digits of the card.")

    class Config:
        schema_extra = {
            "example": {
                "sex": "M",
                "name": "John Doe",
                "bank_name": "Bank of America",
                "credit_card": "VISA CLASSIC",
                "last_code": "1234"
            }
        }

# Function to create the custom message in Spanish
def create_personalized_message_es(data: PersonalData) -> str:
    saludo = "o" if data.sex == "M" else "a"
    last_code_formatted = f"{data.last_code[:2]} {data.last_code[2:]}"
    
    return f"""
    Estimad{saludo} {data.name}, Esta es una notificación de alerta de seguridad de {data.bank_name}.
    Hemos detectado una transacción internacional sospechosa en su tarjeta {data.credit_card} terminada en {last_code_formatted}, Se realizó un cargo por 1,300 pesos con 50 centavos. 
    Si usted no reconoce o no autorizó este cargo, por favor presione 1 para cancelarlo de inmediato.
    Si necesita escuchar este mensaje nuevamente, presione 2. 
    Si prefiere hablar con uno de nuestros representantes de servicio al cliente, presione 3.
    En caso de que usted sí haya realizado esta transacción, no es necesario que haga nada. 
    """

# Function to create the custom message in English
def create_personalized_message_en(data: PersonalData) -> str:
    greeting = "o" if data.sex == "M" else "a"
    last_code_formatted = f"{data.last_code[:2]} {data.last_code[2:]}"
    
    return f"""
    Dear  {data.name},
    This is a security alert notification from {data.bank_name}. 
    We've detected a suspicious international transaction on your card ending in {last_code_formatted}. A charge of 95 dollars and 14 cents has been made.
    If you don’t recognize or didn’t authorize this charge, please press 1 to cancel it immediately.
    If you'd like to hear this message again, press 2.
    If you did make this transaction, there’s no need to take any action.

    """

# Function to generate the audio file
def create_audio(message: str, filename: str, lang: str) -> str:
    tts = gTTS(text=message, lang=lang)
    temp_file = f"{AUDIO_PATH}{filename}.mp3"
    tts.save(temp_file)

    wav_file = f"{AUDIO_PATH}{filename}.wav"
    convert_to_wav(temp_file, wav_file)
    os.remove(temp_file)  # Delete the temporary .mp3 file
    
    return wav_file

# Function to convert audio to 8000 Hz, mono format
def convert_to_wav(input_file, output_file):
    audio = AudioSegment.from_file(input_file)
    audio = audio.set_frame_rate(8000).set_channels(1)
    audio.export(output_file, format="wav")

# Endpoint to generate the audio message in Spanish
@app.post("/call", summary="Enpoint to make a call")
async def generate_audio_es(data: CallParams):
    try:
     await main( data)
     return {"message": "Llamada realizada exitosamente"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al llamar: {e}")


# Endpoint to generate the audio message in Spanish
@app.post("/generate-audio-es", summary="Converts personal data into an audio message in Spanish")
async def generate_audio_es(data: PersonalData):
    try:
        message = create_personalized_message_es(data)
        audio_file = create_audio(message, "welcome_message_es", "es")
        return {"message": "Archivo de audio en español generado exitosamente", "audio_file": audio_file}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generando audio en español: {e}")

# Endpoint to generate the audio message in English
@app.post("/generate-audio-en", summary="Converts personal data into an audio message in English")
async def generate_audio_en(data: PersonalData):
    try:
        message = create_personalized_message_en(data)
        audio_file = create_audio(message, "welcome_message_en", "en")
        return {"message": "Audio file in English generated successfully", "audio_file": audio_file}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating audio in English: {e}")

# Function to create other static messages and their respective audio in Spanish and English
def generate_other_audios():
    static_messages = {
        "message_select_option": {
            "es": "Por favor, seleccione una opción.",
            "en": "Please select an option."
        },
        "message_code_security": {
            "es": "Para cancelar la transacción, primero debe confirmar su identidad. Le hemos enviado un código de seguridad por mensaje de texto a su teléfono. Después del tono, por favor, introduzca solo la parte numérica del código recibido.",
            "en": "To cancel the transaction, please confirm your identity first. We have sent a security code to your phone via text message. After the tone, please enter only the numeric part of the code received."
        },
        "message_invalid_code_security": {
            "es": "El código de seguridad no es válido. Por favor, ingréselo nuevamente después del tono.",
            "en": "The security code is invalid. Please enter it again after the tone."
        },
        "message_transfer": {
            "es": "Por favor, permanezca en línea; en breve uno de nuestros representantes le atenderá.",
            "en": "Please stay on the line; one of our representatives will be with you shortly."
        }
    }
    
    for filename, messages in static_messages.items():
        # Generate Spanish audio
        create_audio(messages["es"], filename + "_es", "es")
        # Generate English audio
        create_audio(messages["en"], filename + "_en", "en")

# Call the function to generate static audios (only once)
generate_other_audios()

generate_other_audios()

#uvicorn app:app --reload --port 8001