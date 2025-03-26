
from aiomqtt import Client
from serial import Serial

import time

from config import MQTT_BROKER, MQTT_PORT, MQTT_USERNAME, MQTT_PASSWORD, ssl_context


class Ports:
    def __init__(self, port_name, baud_rate):
        self.ser = Serial(port_name, baud_rate)

    def clear_buffer(self):
        self.ser.close()
        self.ser.open()
        self.ser.reset_input_buffer()
        self.ser.reset_output_buffer()
        return True

    def send_command(self, command):
        response_lines = []
        self.ser.write((command + '\n').encode())
        time.sleep(1)

        while self.ser.in_waiting > 0:  # Пока есть данные в буфере
            print('working!')
            line = self.ser.readline().decode().strip()
            if line:
                response_lines.append(line)
        return response_lines

    def read(self):
        response_lines = []
        while self.ser.in_waiting > 0:  # Пока есть данные в буфере
            line = self.ser.readline().decode().strip()
            if line:
                response_lines.append(line)
        return '\n'.join(response_lines)


class manageBroker:
    @staticmethod
    async def publish(topic: str, command: str):
        async with Client(
                hostname=MQTT_BROKER,
                port=MQTT_PORT,
                username=MQTT_USERNAME,
                password=MQTT_PASSWORD,
                tls_context=ssl_context,
        ) as client:
            await client.publish(topic, str(command))
            print(f'Отправлено: {command}')


    @staticmethod
    async def subscribe(topic: str):
        async with Client(
                hostname=MQTT_BROKER,
                port=MQTT_PORT,
                username=MQTT_USERNAME,
                password=MQTT_PASSWORD,
                tls_context=ssl_context,
        ) as client:
            await client.subscribe(topic)
            print('Слушаю: ')
            async for msg in client.messages:
                yield msg.payload.decode()





