from gtts import gTTS
from pydub import AudioSegment
import os

# Función para generar el archivo de audio con gTTS
def create_audio(text, filename):
    tts = gTTS(text=text, lang='es')
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
    create_audio("Bienvenido al sistema bancario. Para ventas presione 1, para servicio al cliente presione 2, para hablar con un representante presione 3.", "welcome_message")
    create_audio("Por favor, seleccione una opción.", "please-select")
    create_audio("Por favor, introduzca su código PIN.", "enter-your-pin")
    create_audio("Opción inválida, por favor intente nuevamente.", "invalid-option")
    create_audio("Código PIN inválido.", "invalid-pin")
