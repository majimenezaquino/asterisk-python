from gtts import gTTS
import os

def text_to_speech(text, output_file):
    tts = gTTS(text=text, lang='en')
    tts.save(output_file)
    print(f"Audio file saved as {output_file}")

if __name__ == "__main__":
    text = """Verifica el Canal de Llamada
En tu código, estás originando la llamada a PJSIP/1001, lo cual es correcto si tu softphone está configurado en ese canal. Verifica que el canal coincida con el softphone que estás utilizando.

Con estos pasos adicionales, deberías poder reproducir el audio. Si el problema persiste, revisa los logs de Asterisk para obtener más detalles sobre el error y comparte el mensaje exacto que aparece allí."""
    output_file = "./audios/ivr_message.wav"  # Guardar en el directorio montado
    text_to_speech(text, output_file)