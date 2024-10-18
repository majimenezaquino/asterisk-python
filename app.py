import asyncio
from panoramisk import Manager

async def handle_call(manager):
    originate_action = {
        'Action': 'Originate',
        'Channel': 'PJSIP/1003',
        'Context': 'bank_credit',
        'Exten': 's',
        'Priority': 1,
        'CallerID': 'IVR Test',
        'Timeout': 30000,
        'Async': 'false'
    }

    try:
        response = await manager.send_action(originate_action)
        if response.Response == "Success":
            print("Call initiated:", response)
        else:
            print("Failed to initiate call:", response)
    except Exception as e:
        print(f"Error initiating call: {e}")

async def validate_pin(manager, pin, channel):
    expected_pin = "1234"
    
    if pin == expected_pin:
        print(f"PIN correcto: {pin}")
        result = "valid"
    else:
        print(f"PIN incorrecto: {pin}")
        result = "invalid"

    set_var_action = {
        'Action': 'SetVar',
        'Channel': channel,
        'Variable': 'Result',
        'Value': result
    }
    try:
        await manager.send_action(set_var_action)
    except Exception as e:
        print(f"Error setting variable: {e}")

async def handle_user_event(manager, event):
    if event.UserEvent == 'PinValidation':
        pin = event.get('PIN')
        channel = event.get('Channel')
        department = event.get('Department')
        
        if pin and channel:
            print(f"PIN ingresado por el usuario: {pin}")
            print(f"Departamento seleccionado: {department}")
            await validate_pin(manager, pin, channel)
        else:
            print("Falta información en el evento UserEvent: no se pudo validar el PIN.")

async def main():
    manager = Manager(host='localhost', port=5038, username='python_user', secret='admin')
    
    try:
        # Connect to Asterisk AMI
        await manager.connect()
        
        # Register event handler
        manager.register_event('UserEvent', handle_user_event)
        
        # Initiate the call
        await handle_call(manager)
        
        # Keep the script running
        while True:
            await asyncio.sleep(1)
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        await manager.close()

if __name__ == "__main__":
    asyncio.run(main())