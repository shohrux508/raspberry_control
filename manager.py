import logging
import asyncio
from aiomqtt import Client
from serial import Serial, SerialException
import sys
from config import MQTT_BROKER, MQTT_PORT, MQTT_USERNAME, MQTT_PASSWORD, ssl_context, DEVICE_ID
from telegram_bot_info import InfoBot

# Настройка логирования
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter('[%(asctime)s] %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


class Ports:
    def __init__(self, port_name, baud_rate):
        try:
            self.ser = Serial(port_name, baud_rate, timeout=1)
        except SerialException as e:
            logger.error(f"Ошибка при открытии порта {port_name}: {e}")
            raise

    async def clear_buffer(self):
        try:
            if self.ser.is_open:
                await asyncio.to_thread(self.ser.close)
            await asyncio.to_thread(self.ser.open)
            await asyncio.to_thread(self.ser.reset_input_buffer)
            await asyncio.to_thread(self.ser.reset_output_buffer)
            return True
        except SerialException as e:
            logger.error(f"Ошибка при очистке буфера: {e}")
            return False

    async def _read_response(self):
        """
        Приватный метод для асинхронного чтения данных из последовательного порта.
        """
        response_lines = []
        try:
            while self.ser.in_waiting > 0:
                line = await asyncio.to_thread(self.ser.readline)
                line = line.decode().strip()
                if line and '-' in line:
                    response_lines.append(line)
        except SerialException as e:
            logger.error(f"Ошибка при чтении из порта: {e}")
        return response_lines

    async def send_command(self, command):
        """
        Асинхронно отправляет команду и возвращает ответ, считанный с последовательного порта.
        """
        try:
            await asyncio.to_thread(self.ser.write, (command + '\n').encode())
            await asyncio.sleep(3)
            return await self._read_response()
        except SerialException as e:
            logger.error(f"Ошибка при отправке команды '{command}': {e}")
            return []

    async def read_commands(self):
        """
        Асинхронно считывает команды, используя общий метод _read_response.
        """
        return await self._read_response()


class ManageBroker:
    @staticmethod
    async def publish(topic: str, command: str):
        try:
            async with Client(
                    hostname=MQTT_BROKER,
                    port=MQTT_PORT,
                    username=MQTT_USERNAME,
                    password=MQTT_PASSWORD,
                    tls_context=ssl_context,
            ) as client:
                await client.publish(topic, str(command))
                logger.info(f'Отправлено: {command}')
        except Exception as e:
            logger.error(f"Ошибка при публикации команды '{command}' на тему '{topic}': {e}")

    @staticmethod
    async def subscribe(topic: str):
        attempt = 0

        while attempt < 5:
            try:
                logger.info(f"[MQTT] Подключение к брокеру... Попытка {attempt + 1}")
                async with Client(
                        hostname=MQTT_BROKER,
                        port=MQTT_PORT,
                        username=MQTT_USERNAME,
                        password=MQTT_PASSWORD,
                        tls_context=ssl_context,
                ) as client:
                    await client.subscribe(topic)
                    logger.info(f"[MQTT] Подписка на тему: {topic}")
                    await InfoBot().send(f'Аппарат: {DEVICE_ID} подключился к серверу!')
                    attempt = 0

                    async for msg in client.messages:
                        yield msg.payload.decode()

            except Exception as e:
                attempt += 1
                logger.error(f"[MQTT] Ошибка при подписке: {e}")
                logger.info(f"[MQTT] Повторная попытка через 6 секунд...")
                await asyncio.sleep(6)

        logger.critical("[MQTT] Превышено число попыток подключения. Завершаю.")
        await InfoBot().send(text=f'Аппарат: {DEVICE_ID} - не смог подключиться к серверу, и завершил работу!')
        sys.exit(1)
