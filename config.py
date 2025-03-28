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
MQTT_USERNAME = os.getenv('MQTT_USERNAME')
MQTT_PASSWORD = os.getenv('MQTT_PASSWORD')

ssl_context = ssl.create_default_context()
