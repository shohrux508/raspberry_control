import asyncio
import sys
from config import COMPORT, DEVICE_ID
from manager import Ports, manageBroker

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

serial_port = Ports(port_name=COMPORT, baud_rate=9600)


async def handle_subscription():
    async for message in manageBroker.subscribe(topic=f'devices/{DEVICE_ID}/control'):
        serial_port.send_command(command=message)
        print("Received:", message)


async def main():
    asyncio.create_task(handle_subscription())
    while True:
        await asyncio.sleep(3)  # задержка между публикациями
        response = serial_port.read_commands()
        if len(response) >= 1:
            print(f"ARDUINO: {response}")
        response_text = ','.join(response)
        if '-' in response_text:
            await manageBroker.publish(topic=f'devices/{DEVICE_ID}/response', command=response_text)


if __name__ == "__main__":
    print("Working!")
    asyncio.run(main())