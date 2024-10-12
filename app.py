from asterisk.ami import AMIClient, SimpleAction
from time import sleep

def handle_call():
    client = AMIClient(address='localhost', port=5038)
    future = client.login(username='python_user', secret='admin')

    if future.response.is_error():
        print("Failed to connect to AMI:", future.response)
        return

    # Ejemplo: Escuchar eventos y capturar el DTMF del usuario
    def on_dtmf(event):
        print(f"Received DTMF: {event['Digit']}")
        if event['Digit'] == '1':
            # Hacer algo cuando se recibe '1'
            print("User pressed 1")
        elif event['Digit'] == '2':
            # Hacer algo cuando se recibe '2'
            print("User pressed 2")

    client.add_event_listener(on_dtmf)

    # Realizar la llamada entre softphones (o a través de un IVR)
    action = SimpleAction(
        'Originate',
        Channel='PJSIP/1001',
        Exten='1002',
        Context='internal',
        Priority=1,
        CallerID='Softphone1'
    )

    future = client.send_action(action)
    response = future.response

    print("Call initiated:", response)

    # Mantener la conexión abierta para recibir eventos
    try:
        while True:
            sleep(1)
    except KeyboardInterrupt:
        client.logoff()

if __name__ == "__main__":
    handle_call()
