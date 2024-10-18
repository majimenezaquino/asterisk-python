from asterisk.ami import AMIClient, SimpleAction
from time import sleep

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
        Channel='PJSIP/1003',  # Asegúrate que el canal PJSIP está correcto
        Context='bank_credit',  # Contexto donde se encuentra la lógica del IVR
        Exten='s',              # Usamos 's' para iniciar el IVR desde la extensión de inicio
        Priority=1,
        CallerID='IVR Test',
        Timeout=30000,
        Async=False  # Cambiamos Async a False para evitar duplicación de llamadas
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

def validate_pin(client, pin, channel):
    # Aquí puedes cambiar el PIN a lo que desees validar
    expected_pin = "1234"
    
    if pin == expected_pin:
        print("PIN correcto")
        client.send_action({
            'Action': 'SetVar',
            'Channel': channel,
            'Variable': 'Result',
            'Value': 'valid'
        })
    else:
        print("PIN incorrecto")
        client.send_action({
            'Action': 'SetVar',
            'Channel': channel,
            'Variable': 'Result',
            'Value': 'invalid'
        })

def handle_ivr_pin(client):
    # Aquí manejarías la captura del PIN por DTMF o similar
    # Esperamos recibir un evento de tipo UserEvent desde Asterisk
    def on_user_event(event):
        if event.headers['UserEvent'] == 'PinValidation':
            pin = event.headers['PIN']
            channel = event.headers['Channel']
            print(f"PIN recibido: {pin} para validar")
            validate_pin(client, pin, channel)

    # Registramos el manejador de eventos
    client.register_event('UserEvent', on_user_event)

if __name__ == "__main__":
    # Hacer la llamada desde el IVR
    handle_call()

    # Validar el PIN una vez que el IVR lo reciba
    client = AMIClient(address='localhost', port=5038)
    future = client.login(username='python_user', secret='admin')
    if future.response and not future.response.is_error():
        handle_ivr_pin(client)
    else:
        print("No se pudo conectar a AMI para manejar el PIN.")
