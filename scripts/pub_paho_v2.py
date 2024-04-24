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
counter = 10
MAX_SIZE = 60 * 1024  # 60 KB
message = "A" * 1 # This generates an interesting behavior in the broker, exchanging a lot of ACKs
i=0
while i < 10:
    # sensor_data = random.randint(0, 999)
    client.publish(topic, message, qos=2, retain=True)
    #print(f"Message {counter} published to {topic}: {sensor_data}")
    i += 1
    time.sleep(0.01)  # Wait before next publish

