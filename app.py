from gtts import gTTS
from asterisk.ami import AMIClient, SimpleAction
from time import sleep
import os

def text_to_speech(text, output_file):
    tts = gTTS(text=text, lang='en')
    tts.save(output_file)
    print(f"Audio file saved as {output_file}")

def handle_call():
    # Conectar al AMI de Asterisk
    client = AMIClient(address='localhost', port=5038)
    future = client.login(username='python_user', secret='admin')

    if not future.response or future.response.is_error():
        print("Failed to connect to AMI:", future.response)
        return

    # Originate una llamada que active el IVR en la extensión 1001
    action = SimpleAction(
        'Originate',
        Channel='PJSIP/1001',
        Context='internal',
        Exten='1001',
        Data='ivr_message',
        Priority=1,
        CallerID='IVR Test',
        Timeout=30000,
        Async=True
    )

    # Enviar la acción al AMI
    future = client.send_action(action)
    response = future.response

    if response:
        print("Call initiated:", response)
    else:
        print("No response received from Asterisk")

    try:
        while True:
            sleep(1)
    except KeyboardInterrupt:
        client.logoff()

if __name__ == "__main__":
    text = """Verifica el Canal de Llamada
En tu código, estás originando la llamada a PJSIP/1001, lo cual es correcto si tu softphone está configurado en ese canal. Verifica que el canal coincida con el softphone que estás utilizando.

Con estos pasos adicionales, deberías poder reproducir el audio. Si el problema persiste, revisa los logs de Asterisk para obtener más detalles sobre el error y comparte el mensaje exacto que aparece allí."""
    output_file = "audios/ivr_message.wav"
    
    # Convertir texto a voz y guardar el archivo
    text_to_speech(text, output_file)

    # Hacer la llamada desde el IVR
    handle_call()
