# test_manager.py
import asyncio
import pytest
from unittest.mock import patch
import manager


# Фиктивный класс, имитирующий поведение serial.Serial
class DummySerial:
    def __init__(self, port, baud_rate, timeout=1):
        self.port = port
        self.baud_rate = baud_rate
        self.timeout = timeout
        self.is_open = True
        self.in_waiting = 0
        self._buffer = []

    def close(self):
        self.is_open = False

    def open(self):
        self.is_open = True

    def reset_input_buffer(self):
        self._buffer = []
        self.in_waiting = 0

    def reset_output_buffer(self):
        pass

    def write(self, data):
        # Для тестирования: если команда содержит "TEST", заполняем буфер ответом
        command = data.decode().strip()
        if "TEST" in command:
            self._buffer.append(b"TEST-RESPONSE\n")
            self.in_waiting = len(self._buffer[0])

    def readline(self):
        if self._buffer:
            line = self._buffer.pop(0)
            # Если буфер пуст, сбрасываем счетчик in_waiting
            self.in_waiting = 0
            return line
        return b""


# Фикстура для замены serial.Serial на DummySerial в модуле manager
@pytest.fixture
def dummy_serial(monkeypatch):
    monkeypatch.setattr(manager, 'Serial', DummySerial)
    ports = manager.Ports("dummy_port", 9600)
    return ports


@pytest.mark.asyncio
async def test_clear_buffer(dummy_serial):
    result = await dummy_serial.clear_buffer()
    assert result is True
    assert dummy_serial.ser.is_open is True


@pytest.mark.asyncio
async def test_send_command(dummy_serial):
    # Отправляем команду, которая в DummySerial вызывает добавление ответа в буфер
    response = await dummy_serial.send_command("TEST")
    # Проверяем, что в ответе содержится ожидаемая строка
    assert any("TEST-RESPONSE" in line for line in response)


@pytest.mark.asyncio
async def test_read_commands(dummy_serial):
    # Заполняем буфер вручную
    dummy_serial.ser._buffer.append(b"DATA-RESPONSE\n")
    dummy_serial.ser.in_waiting = len(dummy_serial.ser._buffer[0])
    response = await dummy_serial.read_commands()
    assert any("DATA-RESPONSE" in line for line in response)
