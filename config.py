import ssl

MQTT_BROKER = '3dc6927eb43a444ebbac794961b9b974.s1.eu.hivemq.cloud'
MQTT_PORT = 8883
TOPIC_PUB = 'devices/response'
TOPIC_SUB = 'devices/control'
MQTT_USERNAME = 'hivemq.webclient.1742899651883'
MQTT_PASSWORD = '2j3$<7SYRA&m!v9wLVfn'

ssl_context = ssl.create_default_context()