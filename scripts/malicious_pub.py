#!/usr/bin/python3
'''
Extended program that executes the TCP three-way handshake using scapy and
then proceeds to send an MQTT CONNECT and a PUBLISH message with QoS 2,
waits for PUBREC but intentionally omits PUBREL.

We should drop incoming w/ iptables -A OUTPUT -p tcp --tcp-flags RST RST -j DROP
missing:  
    - implenment better log
    - Parse connack (OK)
Based on scapy/normal_tcp_session.py
'''

import logging
import sys
#import lib_scapy
from scapy.all import *
from scapy.contrib.mqtt import *
from scapy.layers.inet import IP, TCP
import netifaces as ni
import random


# Define the broker IP and the TCP port
broker_ip = '192.168.122.48'
broker_port = 1883
num_messages = 1  # Number of MQTT messages to DoS flood the queue with

# Functions for MQTT packet crafting
def craft_mqtt_connect(client_id="ScapyClient"):
    # proto_name = b"\x00\x04MQTT"
    # proto_level = b"\x04"
    # connect_flags = b"\x02"  # Clean session
    # keep_alive = b"\x00\x3c"  # 60 seconds
    # client_id_length = struct.pack("!H", len(client_id))
    # payload = client_id_length + client_id.encode()
    # remaining_length = len(proto_name) + 1 + 1 + 2 + len(payload)
    # packet = b"\x10" + bytes([remaining_length]) + proto_name + proto_level + connect_flags + keep_alive + payload
    # Protocol Name: "MQTT"
    #proto_name = "MQTT"
    # Protocol Level: 4 (MQTT 3.1.1)
    #proto_level = 4
    # Connect Flags: 2 (Clean Session)
    #connect_flags = 2
    # Keep Alive: 60 seconds
    keep_alive = 60

    return scapy.contrib.mqtt.MQTTConnect(
        klive=keep_alive,
    )


def craft_mqtt_publish(topic, message, packet_id=1, qos=2):

    # topic_length = struct.pack("!H", len(topic))
    # packet_id_bytes = struct.pack("!H", packet_id)
    # fixed_header = b"\x34"  # PUBLISH, DUP=0, QoS=2, RETAIN=0 (0b0011 0 10 0)
    # var_header = topic_length + topic.encode() + packet_id_bytes
    # payload = message.encode()
    # remaining_length = len(var_header) + len(payload) # what if bigger than 127?
    # packet = fixed_header + bytes([remaining_length]) + var_header + payload
    return scapy.contrib.mqtt.MQTTPublish(topic=topic,
                                          QOS=qos,
                                          id=packet_id,
                                          value=message)

# Get the IP address of eth2 interface, the one we are using in the lab
# can be automated to get the IP of the interface that is up
ni.ifaddresses('eth2')
ip = ni.ifaddresses('eth2')[ni.AF_INET][0]['addr']

# Manually setting the values for our specific case

si = ip  # Source IP address
sp = random.randint(0, 0xFFFF)   # Source port, implemented random value due to binding error
di = broker_ip  # Destination IP address
dp = broker_port              # Destination port (standard MQTT port)
cseq = random.randint(0, 0xFFFFFFFF)  # Generate a random 32-bit sequence number
debug = 10 # Debug level (e.g., 30 for WARNING)
return_code = 0        # Indicate successful initialization
return_string = "Initialization successful"

# Our default logging is at WARNING level
# 10: DEBUG, 20: INFO, 30: WARNING, 40:ERROR, 50: CRITICAL
# Logging setup
logging_level = debug 
logging.basicConfig(stream=sys.stderr, level=logging_level)
mylog = logging.getLogger("mainlogger")
mylog.warning("Program starts")


# Setting the debug level according to a possible value provided as an argument
mylog.setLevel(debug)
# If the debug level is higher than the INFO level, ie 20, then we put
# scapy in non verbose mode (nothing goes to stdout after sr1() and send() )
if debug>20:
    scapy_verbose=0
else:
    scapy_verbose=10


# At this point, we know that si and di are either an IP or a resolvable name
# We do not know if we have a route to reach them
# We do not know if si is the same as the host we execute the code from
# We know that sp and dp are within acceptable margins for a port
# We know that cseq is within acceptable range for a sequence number [0:2**32]
# A negative return code means that something went wrong with the args
# we have to abort the execution

if return_code < 0:
    mylog.critical(return_string)
    exit()

# ##########################
# Beginning of the main execution after the preliminaries
# ##########################
mylog.debug("src IP = %s ; src port = %s", si, sp)
mylog.debug("dst IP = %s ; dst port = %s", di, dp)
mylog.debug("inital seq number = %s",cseq)

# SYN PACKET
synpkt = IP(src=si, dst=di) / TCP (seq=cseq, sport=sp, dport=dp)
mylog.debug("synpkt %s", synpkt.summary())
pair, unans = sr(synpkt, verbose=scapy_verbose)
# Beware .. we could be waiting forever ..


mylog.info("SYN packet sent")
if len(pair) != 1:
    mylog.critical("We have received %s answers to the SYN pckt instead of 1.\nAborting", len(pair))
    exit()
if str(pair[0][1][TCP].flags)=="SA":
    mylog.info("SYN ACK packet received")
    synackpkt=pair[0][1]
else:
    mylog.critical("Response to the SYN Packet had the %s flags instead of SYN ACK", str(pair[0][1][TCP].flags))
    exit()
    
# ACK PACKET
ackpkt = synpkt.copy()
ackpkt[TCP].seq = ackpkt[TCP].seq + 1 # @todo: why +1?
ackpkt[TCP].flags = "A"
ackpkt[TCP].ack=synackpkt[TCP].seq + 1
# normally, the server does not reply to the ACK
# thus we use send() instead of sr() which would be waiting forever
# (or for some timeout)
send(ackpkt, verbose=scapy_verbose)
mylog.info("ACK packet sent")
# If the server sends a RST, because, eg, we forgot the iptables rule
# and the client has sent a RST .. we will miss that packet and will
# continue, unaware of what is going on.

# Checks TCP connection. @TODO: Would this be a problem on 1883?

datapkt=ackpkt.copy()
datapkt[TCP].flags="PA"
text = "hello world"
datapkt = datapkt / Raw(load=text)
# the DATA packet should be acknowledged if everything goes well
# Thus, we can use sr() and check what we got back
pair, unans = sr(datapkt, verbose=scapy_verbose)
mylog.info("DATA packet sent")

# Extracting the sequence number and SYN flag from the reply
if len(pair) != 1:
    mylog.critical("We have received %s answers to DATA packet instead of 1.\nAborting", len(pair))
    exit()
if str(pair[0][1][TCP].flags)=="A":
    mylog.info("ACK packet received")
    dataackpkt=pair[0][1]
    expected_ack=datapkt[TCP].seq + len(datapkt[TCP].payload)
    if expected_ack != dataackpkt[TCP].ack:
        mylog.critical("Wrong ACK value from the server: got %s instead of the expected %s value. \nAborting", dataackpkt[TCP].ack, expected_ack)
        exit()
else:
    mylog.critical("Response to the DATA Packet had the %s flags instead of ACK \n===>You probably forgot to prevent your client from emitting a RST packet.\n\"iptables -A OUTPUT -p tcp --tcp-flags RST RST -j DROP\"\n\nAborting", str(pair[0][1][TCP].flags))
    exit()
mylog.info("data packet sent with %s bytes: \'%s\'", len(text), text)

# Extracting the sequence number if everything went well
# @TODO: look here
#cseq = expected_ack

# MQTT part starts
mqtt_connect_packet = craft_mqtt_connect()
mylog.info("Sending MQTT CONNECT packet")

# Sends CONNECT and checks CONNACK
connack_pkt = sr1(IP(mqtt_connect_packet), verbose=scapy_verbose)
# # TODO: is this useful?
# connack_pkt = sniff(filter=f"tcp and src {di} and dst {si} and port {sp}", count=1, timeout=5)
# if connack_pkt and connack_pkt[0].haslayer(TCP) and connack_pkt[0].haslayer(Raw):
#     if connack_pkt[0][Raw].load[0] == 0x20:
#         mylog.info("Received CONNACK packet")
#     else:
#         mylog.error("No CONNACK received, or response malformed.")
# else:
#     mylog.error("No CONNACK received within timeout period.")
# time.sleep(1)

# Update seq and ack numbers based on CONNACK
#cseq += len(connack_pkt[Raw].load)

#for i in range(1, num_messages + 1):

# MQTT PUBLISH with QoS 2
mqtt_publish_packet = craft_mqtt_publish("test/topic", "Test QoS 2 message")
mylog.info("Sending MQTT PUBLISH packet with QoS 2")
pubrec_pkt = sr1(IP(mqtt_publish_packet), verbose=scapy_verbose)

# cseq += len(mqtt_publish_packet)
# Log sending PUBLISH and receiving PUBREC
mylog.info(f"Sent PUBLISH, waiting for PUBREC...")

if pubrec_pkt and Raw in pubrec_pkt and pubrec_pkt[Raw].load[0] == 0x50:  # 0x50 = PUBREC
    mylog.info(f"Received PUBREC for message ")
else:
    mylog.error("No PUBREC received, or response malformed.")


'''
# We will never reach this place if the server sends nothing back ...:-(
if len(pair) != 1:
    mylog.critical("We have received %s answers to DATA packet instead of 1.\nAborting", len(pair))
    exit()
if str(pair[0][1][TCP].flags)=="A":
    mylog.info("ACK packet received")
    dataackpkt=pair[0][1]
    expected_ack=datapkt[TCP].seq + len(datapkt[TCP].payload)
    if expected_ack != dataackpkt[TCP].ack:
        mylog.critical("Wrong ACK value from the server: got %s instead of the expected %s value. \nAborting", dataackpkt[TCP].ack, expected_ack)
        exit()
else:
    mylog.critical("Response to the DATA Packet had the %s flags instead of ACK \n===>You probably forgot to prevent your client from emitting a RST packet.\n\"iptables -A OUTPUT -p tcp --tcp-flags RST RST -j DROP\"\n\nAborting", str(pair[0][1][TCP].flags))
    exit()
mylog.info("data packet sent with %s bytes: \'%s\'", len(text), text)
'''
# FIN/ACK PACKET
finpkt = pubrec_pkt.copy()
finpkt[TCP].flags = "FA"
finpkt[TCP].seq = cseq + len(finpkt[TCP].payload)
finpkt[TCP].remove_payload()
serverfinpkt = sr1(finpkt, verbose=scapy_verbose)

# We could check here that we did get what we were expecting from the server
# Instead of blinding trusting whatever packet has been received
# ACK PACKET 
finfinpkt=finpkt.copy()
finfinpkt[TCP].flags="A"
finfinpkt[TCP].seq = finfinpkt[TCP].seq +1
finfinpkt[TCP].ack = finfinpkt[TCP].ack +1
send(finfinpkt, verbose=scapy_verbose)
mylog.warning("Program Ends successfully")

