import time
import random

import paho.mqtt.client as mqtt

# This should be static
broker_address = "192.168.122.48" 
topic = "sensor/data" 

# create new client instance
client = mqtt.Client("P1")  
client.connect(broker_address) 

# Publish sensor data with QoS 2 and retain flag
counter = 100
MAX_SIZE = 60 * 1024  # 60 KB
message = "A" * MAX_SIZE # This generates an interesting behavior in the broker, exchanging a lot of ACKs

for i in range(counter):
    # sensor_data = random.randint(0, 999)
    client.publish(topic, message, qos=1, retain=True)
    print(f"Message {i} published to {topic}")
    time.sleep(0.01)  # Wait for 5 seconds before next publish

