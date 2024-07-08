'''
File: pub_paho_v2.py
Author: Erick Silva
Course: CS231
This script is part of the coursework for CS231. It is used to publish sensor data 
to a specific MQTT topic using the Paho MQTT client version 2.0.
'''

import time

import paho.mqtt.client as mqtt

# Based on: https://eclipse.dev/paho/files/paho.mqtt.python/html/migrations.html
# This should be static
broker_address = "localhost" 
topic = "sensor/data"

# create new client instance
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="P1")
client.connect(broker_address) 

# Publish sensor data with QoS 2 and retain flag
counter = 100
MAX_SIZE = 60 * 1024  # 60 KB
message = "A" * MAX_SIZE # This generates an interesting behavior in the broker, exchanging a lot of ACKs

for i in range(counter):
    # sensor_data = random.randint(0, 999)
    client.publish(topic, message, qos=1, retain=True)
    print(f"Message {i} published to {topic}")
    time.sleep(0.01)  # Wait before next publish, increasing this didnt made it work

