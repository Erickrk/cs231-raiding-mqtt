import time
import random

import paho.mqtt.client as mqtt

# Based on: https://eclipse.dev/paho/files/paho.mqtt.python/html/migrations.html

# This should be static
broker_address = "192.168.122.48" 
topic = "sensor/data"

# create new client instance
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="P1")
client.connect(broker_address) 


# Publish sensor data with QoS 2 and retain flag
MAX_SIZE = 240 * 1024  # 60 KB
message = "A" * MAX_SIZE # This generates an interesting behavior in the broker, exchanging a lot of ACKs

counter = 100000
i=0
while i < counter:
    # sensor_data = random.randint(0, 999)
    client.publish(topic, message, qos=2, retain=True)
    print(f"Message {i} published to {topic}: {message}")
    i += 1
    time.sleep(0.01)  # Wait before next publish, increasing this didnt made it work

