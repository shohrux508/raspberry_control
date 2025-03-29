import ssl
from dotenv import load_dotenv
import os

load_dotenv()

COMPORT = os.getenv('COMPORT')
DEVICE_ID = os.getenv("DEVICE_ID")
MQTT_BROKER = os.getenv('MQTT_BROKER')
MQTT_PORT = int(os.getenv('MQTT_PORT'))
TOPIC_SUB = os.getenv('TOPIC_SUB')
TOPIC_PUB = os.getenv('TOPIC_PUB')
TOPIC_ST = os.getenv('TOPIC_ST')
MQTT_USERNAME = os.getenv('MQTT_USERNAME')
MQTT_PASSWORD = os.getenv('MQTT_PASSWORD')
BOT_TOKEN = os.getenv('TELEGRAM_INFO_BOT_TOKEN')
ADMIN_ID = os.getenv('TELEGRAM_INFO_BOT_ADMIN_ID')

ssl_context = ssl.create_default_context()
