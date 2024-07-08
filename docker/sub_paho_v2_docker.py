'''
    File: sub_paho_v2.py
    Author: Erick Silva
    Course: CS231
    This script is part of the coursework for CS231. It is used to subscribe to a sensor data
    specific MQTT topic using the Paho MQTT client version 2.0.
'''
#@TODO: currently sub not working but connected
import paho.mqtt.client as mqtt

# The callback for when the client receives a CONNACK response from the server.


# NEW code for both version
def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code == 0:
        print("Connected with result code " + str(rc))
        client.subscribe("sensor/data", qos=1)  # Subscribe to the sensor data topic with QoS 2
    if reason_code > 0:
        print("Failed to connect due to error " + str(rc))


# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    print(f"Received message: {msg.payload.decode()} on topic {msg.topic}")


# Configure the MQTT client
local_bind_address = "172.17.0.1"
broker_address = "172.17.0.2"

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="S1")  # create new instance
#client.on_connect = on_connect(client=None, userdata=None, flags=None, reason_code=None, properties=None)
client.on_message = on_message

client.connect(broker_address, bind_address=local_bind_address)  # connect to broker with QoS 2
client.subscribe("sensor/data", qos=1)  # Subscribe to the sensor data topic with QoS 2

# Blocking call that processes network traffic, dispatches callbacks and handles reconnecting.
client.loop_forever()
