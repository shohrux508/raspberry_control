import asyncio
import sys

from config import COMPORT
from manager import Ports, manageBroker

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

serial_port = Ports(port_name=COMPORT, baud_rate=9600)


async def handle_subscription():
    async for message in manageBroker.subscribe(topic='devices/1/control'):
        serial_port.send_command(command=message)
        print("Received:", message)


async def main():
    asyncio.create_task(handle_subscription())
    while True:
        await asyncio.sleep(5)  # задержка между публикациями
        response = (serial_port.send_command(command='get-status'))
        await manageBroker.publish(topic='devices/1/response', command=response)
        print("Published: True")


if __name__ == "__main__":
    print("Working!")
    asyncio.run(main())
