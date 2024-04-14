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
try:
    while True:
        sensor_data = random.randint(0, 999)
        client.publish(topic, sensor_data, qos=2, retain=True)
        print(f"Data published to {topic}: {sensor_data}")
        #time.sleep(5)  # Wait for 5 seconds before next publish
except KeyboardInterrupt:
    print("Publisher stopped.")
