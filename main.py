from aiomqtt import Client
import asyncio
import sys
from config import MQTT_BROKER, MQTT_PORT, TOPIC_PUB, TOPIC_SUB, MQTT_USERNAME, MQTT_PASSWORD, ssl_context, COMPORT
from manager import Ports

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

serial_port = Ports(port_name=COMPORT, baud_rate=9600)

async def main():
    async with Client(
        hostname=MQTT_BROKER,
        port=MQTT_PORT,
        username=MQTT_USERNAME,
        password=MQTT_PASSWORD,
        tls_context=ssl_context,
    ) as client:

        await client.subscribe(TOPIC_SUB)
        print(f"Подписан на {TOPIC_SUB}")

        async for msg in client.messages:
            command = msg.payload.decode()
            print(f"Получена команда: {command}")
            serial_response = serial_port.send_command(command)
            if isinstance(serial_response, list):
                serial_response = "\n".join(serial_response)
            await client.publish(TOPIC_PUB, 'caught'.encode())
            print(f"Ответ отправлен: {serial_response}")

if __name__ == "__main__":
    asyncio.run(main())

