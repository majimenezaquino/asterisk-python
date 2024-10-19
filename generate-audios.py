from gtts import gTTS
from pydub import AudioSegment
import os


# Función para generar el archivo de audio con gTTS
def create_audio(text, filename):
    tts = gTTS(text=text, lang="en")
    temp_file = f"./audios/{filename}.mp3"  # Archivo temporal en formato mp3
    tts.save(temp_file)
    convert_to_wav(temp_file, f"./audios/{filename}.wav")  # Convertir a formato WAV


# Función para convertir el archivo de audio a formato 8000 Hz, mono
def convert_to_wav(input_file, output_file):
    audio = AudioSegment.from_file(input_file)
    audio = audio.set_frame_rate(8000).set_channels(1)  # Convertir a 8000 Hz y mono
    audio.export(output_file, format="wav")  # Exportar como archivo WAV
    os.remove(input_file)  # Eliminar el archivo temporal .mp3
    print(f"Convertido {output_file} a formato compatible con Asterisk.")


if __name__ == "__main__":
    welcome_message = """

        Dear {name}, this is an automated notification about your {bank_card} card ending in {last_code}. 
        A foreign transaction of two hundred sixty-one dollars and thirty-one cents has been made. 
        If you recognize this transaction, no further action is needed. If you do not recognize this transaction, press 1 to report it. 
        Press 2 to be transferred to the Fraud Department.  Or press 3 to hear this message again.   
        Please select an option.
    """.format(
        name="Ramon Perez", bank_card="VISA CLASSIC Banesco", last_code="1234"
    )

    create_audio(welcome_message, "welcome_message")
    create_audio(
        "You are being transferred to the Customer Service Department. Please stay on the line while we connect you with a representative.",
        "transferred_customer_service",
    )
    create_audio(
        "You are being transferred to the Fraud Department. Please stay on the line while we connect you with a representative.",
        "transferred_fraud_department",
    )

    create_audio("Código PIN inválido.", "invalid-pin")
