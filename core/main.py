import asyncio
import sys
from aiomqtt import Client

from core.config import MQTT_BROKER, MQTT_PORT, MQTT_USERNAME, MQTT_PASSWORD, ssl_context, TOPIC_SUB, TOPIC_PUB

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


async def main():
    client = Client(
        hostname=MQTT_BROKER,
        port=MQTT_PORT,
        username=MQTT_USERNAME,
        password=MQTT_PASSWORD,
        tls_context=ssl_context
    )

    async with client:
        await client.subscribe(TOPIC_SUB)
        print(f"{TOPIC_SUB} -- subscribed successfully")

        async for msg in client.messages:
            command = msg.payload.decode()
            print(f"Received command: {command}")

            await asyncio.sleep(1)
            response = f"Done: {command}"
            await client.publish(TOPIC_PUB, response.encode())
            print(f"Answered: {response}")


async def send_command(text: str):
    async with Client(
            hostname=MQTT_BROKER,
            port=MQTT_PORT,
            username=MQTT_USERNAME,
            password=MQTT_PASSWORD,
            tls_context=ssl_context
    ) as client:
        await client.publish(TOPIC_SUB, text.encode())
        print(f"Command sent to {TOPIC_SUB}: {text}")


if __name__ == "__main__":
    asyncio.run(main())
