'''
    File: sub_paho_v1.py
    Author: Erick Silva
    Course: CS231
    This script is part of the coursework for CS231. It is used to subscribe to a sensor data
    specific MQTT topic using the Paho MQTT client version 1.3.
'''
import paho.mqtt.client as mqtt

# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))
    client.subscribe("sensor/data", qos=2)  # Subscribe to the sensor data topic with QoS 2

# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    print(f"Received message: {msg.payload.decode()} on topic {msg.topic}")

# Configure the MQTT client
broker_address = "172.17.0.2" 
client = mqtt.Client("C1")  # create new instance
client.on_connect = on_connect
client.on_message = on_message

client.connect(broker_address)  # connect to broker with QoS 2

# Blocking call that processes network traffic, dispatches callbacks and handles reconnecting.
client.loop_forever()
