import asyncio
import sys
import signal
import logging
from config import COMPORT, DEVICE_ID
from manager import Ports, ManageBroker

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

class Application:
    """
    Класс Application инкапсулирует основную логику приложения,
    включая инициализацию последовательного порта, управление подписками MQTT
    и основным циклом обработки команд.
    """
    def __init__(self, comport: str, device_id: str, baud_rate: int = 9600):
        """
        Инициализирует компоненты приложения.

        :param comport: Имя последовательного порта.
        :param device_id: Идентификатор устройства для MQTT.
        :param baud_rate: Скорость передачи данных (по умолчанию 9600).
        """
        self.comport = comport
        self.device_id = device_id
        self.serial_port = Ports(port_name=self.comport, baud_rate=baud_rate)
        self.shutdown_event = asyncio.Event()
        self.subscription_task = None

    async def handle_subscription(self):
        """
        Обрабатывает входящие MQTT-сообщения для управления устройством.
        Каждое полученное сообщение передаётся в последовательный порт.
        """
        try:
            async for message in ManageBroker.subscribe(topic=f'devices/{self.device_id}/control'):
                await self.serial_port.send_command(command=message)
                logger.info("Received: %s", message)
        except Exception as e:
            logger.error("Error in subscription handler: %s", e)

    async def run(self):
        """
        Запускает основную логику приложения.
        Создаёт задачу подписки и в основном цикле обрабатывает команды.
        """
        self.subscription_task = asyncio.create_task(self.handle_subscription())
        try:
            while not self.shutdown_event.is_set():
                await asyncio.sleep(3)  # Задержка между публикациями
                response = await self.serial_port.read_commands()
                if response:
                    logger.info("ARDUINO: %s", response)
                response_text = ','.join(response)
                if '-' in response_text:
                    await ManageBroker.publish(topic=f'devices/{self.device_id}/response', command=response_text)
        except Exception as e:
            logger.error("Error in main loop: %s", e)
        finally:
            self.subscription_task.cancel()
            await asyncio.gather(self.subscription_task, return_exceptions=True)
            logger.info("Shutdown complete.")

    def shutdown(self):
        """
        Инициирует корректное завершение работы приложения.
        """
        logger.info("Shutdown signal received.")
        self.shutdown_event.set()

def setup_signal_handlers(app: Application, loop: asyncio.AbstractEventLoop):
    """
    Устанавливает обработчики сигналов для корректного завершения приложения.

    :param app: Экземпляр Application.
    :param loop: Событийный цикл.
    """
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, app.shutdown)
        except NotImplementedError:
            # На Windows add_signal_handler может быть не поддержан
            pass

if __name__ == "__main__":
    logger.info("Working!")
    app = Application(comport=COMPORT, device_id=DEVICE_ID)
    loop = asyncio.get_event_loop()
    setup_signal_handlers(app, loop)
    try:
        loop.run_until_complete(app.run())
    finally:
        loop.close()
