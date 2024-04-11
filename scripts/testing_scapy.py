from scapy.all import *
from scapy.layers.inet import IP, TCP
from scapy.contrib.mqtt import *

# Set the target broker details
broker_ip = "192.168.122.48"
broker_port = 1883
import random

# Create an IP packet destined for the broker
ip = IP(dst=broker_ip)

# Generate a random source port for our end of the connection
src_port = random.randint(0, 0xFFFF)   # Source port, implemented random value due to binding error


# Establish a TCP connection (SYN, SYN+ACK, ACK)
syn = TCP(sport=src_port, dport=broker_port, flags='S', seq=RandInt())
syn_ack = sr1(ip/syn)
ack = TCP(sport=src_port, dport=broker_port, flags='A', seq=syn_ack.ack, ack=syn_ack.seq + 1)
send(ip/ack)

# Now that the TCP connection is established, we can send MQTT packets
# Craft an MQTT CONNECT packet
connect_pkt = MQTT()/MQTTConnect(clientId="ScapyClient")
send(ip/TCP(sport=src_port, dport=broker_port, flags="PA", seq=ack.seq, ack=ack.ack)/connect_pkt)

# Wait a bit for the broker to process our connection
time.sleep(2)

# Craft an MQTT PUBLISH packet to send a message
topic = "test/topic"
message = "Hello from Scapy"
publish_pkt = MQTT()/MQTTPublish(topic=topic, value=message)
send(ip/TCP(sport=src_port, dport=broker_port, flags="PA", seq=ack.seq + len(connect_pkt), ack=ack.ack)/publish_pkt)

# If you want to subscribe instead of publish, use MQTTSubscribe
# subscribe_pkt = MQTT()/MQTTSubscribe(topics=[MQTTTopic(topic="test/topic")])
# send(ip/TCP(sport=src_port, dport=broker_port, flags="PA", seq=ack.seq + len(connect_pkt), ack=ack.ack)/subscribe_pkt)

# Remember to properly close the TCP connection when done
# This is an example and does not handle MQTT session closure or TCP teardown sequences
