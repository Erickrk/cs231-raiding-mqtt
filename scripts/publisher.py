import paho.mqtt.client as mqtt
import time

# This should be static
broker_address = "20.20.20.48" 
topic = "sensor/data" 

# create new client instance
client = mqtt.Client("P1")  
client.connect(broker_address) 

# Publish sensor data
try:
    while True:
        sensor_data = 100  # Dummy sensor data
        client.publish(topic, sensor_data)
        print(f"Data published to {topic}: {sensor_data}")
        time.sleep(5)  # Wait for 5 seconds before next publish
except KeyboardInterrupt:
    print("Publisher stopped.")
