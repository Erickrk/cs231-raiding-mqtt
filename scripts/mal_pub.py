'''
# subscribe_pkt = MQTT()/MQTTSubscribe(topics=[MQTTTopic(topic="test/topic")])
# send(ip/TCP(sport=src_port, dport=broker_port, flags="PA", seq=ack.seq + len(connect_pkt), ack=ack.ack)/subscribe_pkt)
We should drop incoming w/ iptables -A OUTPUT -p tcp --tcp-flags RST RST -j DROP
'''

from scapy.all import *
from scapy.layers.inet import IP, TCP
from scapy.contrib.mqtt import *
import random

broker_ip = "192.168.122.48"
broker_port = 1883
number_packets = 3000

# MQTT Connect Packet for version 3.1.1
def create_connect_packet(client_id="cm"):
    # Protocol Name and Level for MQTT 3.1.1
    proto_name = "MQTT"
    proto_level = 4  # 4 indicates MQTT 3.1.1

    # Connect Flags
    # Assuming Clean Session, and No Will, Username, or Password
    username_flag = 0
    password_flag = 0
    will_retain = 0
    will_qos = 0
    will_flag = 0
    clean_session = 0
    reserved = 0
    # Calculating the Connect Flags byte
    connect_flags = (username_flag << 7 | password_flag << 6 |
                     will_retain << 5 | will_qos << 3 |
                     will_flag << 2 | clean_session << 1 | reserved)

    # Keep Alive timer (in seconds)
    keep_alive = 255
    keep_alive_high_byte = (keep_alive >> 8) & 0xFF  # Shift right by 8 bits to get the high byte
    keep_alive_low_byte = keep_alive & 0xFF  # Mask with 0xFF to get the low byte

    # Client ID
    # Length of the Client ID followed by the Client ID string
    client_id_length = len(client_id)

    # Assembling the Variable Header
    ''' @TODO: fix this comment
    !: This specifies that the data should be packed in network (big-endian) byte order.
    H: This stands for an unsigned short integer, which is 2 bytes. It's used for the length of the protocol name.
    6s: This stands for a string of 6 characters. It's used for the protocol name itself, which is "MQTT".
    B: This stands for an unsigned char, which is 1 byte. It's used twice, first for the protocol level and then for the connect flags.
    H: This is used again for the length of the client ID.
    '''
    variable_header = struct.pack("!H4sBBBB", len(proto_name), proto_name.encode(), proto_level, connect_flags,
                                  keep_alive_high_byte, keep_alive_low_byte)

    # Payload
    payload = struct.pack("!H2s", client_id_length, client_id.encode())

    # Fixed Header for CONNECT
    # MQTT Packet Type for CONNECT is 1
    packet_type = 1 << 4  # Shifting 4 bits left to position the packet type
    remaining_length = len(variable_header) + len(payload)  # Remaining Length

    # Remaining Length Encoding (can be 1-4 bytes, here simplified to 1 byte for lengths < 128)
    if remaining_length > 127:
        raise ValueError("Packet too long")

    fixed_header = struct.pack("!BB", packet_type, remaining_length)

    # Final MQTT CONNECT Packet
    connect_packet = fixed_header + variable_header + payload
    return Raw(load=connect_packet)

# MQTT Publish Packet
def create_publish_packet(topic="test/topic", message="Hello MQTT"):
    pkt = MQTT()/MQTTPublish(topic=topic, value=message)
    # pkt.len = len(topic) + len(message) + 2 
    return pkt

# Create an IP packet destined for the broker
ip = IP(dst=broker_ip)

# Generate a random source port for our end of the connection
src_port = random.randint(0, 0xFFFF)   # Source port, implemented random value due to binding error


# Establish a TCP connection (SYN, SYN+ACK, ACK)
def establish_tcp_connection(ip, src_port, broker_port):
    syn = TCP(sport=src_port, dport=broker_port, flags='S', seq=RandInt())
    syn_ack = sr1(ip/syn)
    ack = TCP(sport=src_port, dport=broker_port, flags='A', seq=syn_ack.ack, ack=syn_ack.seq + 1)
    send(ip/ack)
    return ack

# Close the TCP connection (FIN, FIN+ACK, ACK)
def close_tcp_connection(ip, src_port, broker_port, seq, ack):
    fin = TCP(sport=src_port, dport=broker_port, flags='FA', seq=seq, ack=ack.ack)
    fin_ack = sr1(ip/fin)
    ack = TCP(sport=src_port, dport=broker_port, flags='A', seq=fin_ack.ack, ack=fin_ack.seq + 1)
    send(ip/ack)

ack = establish_tcp_connection(ip, src_port, broker_port)
# Craft an MQTT CONNECT packet
connect_pkt = create_connect_packet()
send(ip/TCP(sport=src_port, dport=broker_port, flags="PA", seq=ack.seq, ack=ack.ack)/connect_pkt)

# Wait a bit for the broker to process our connection
#time.sleep(2)
seq = ack.seq + len(connect_pkt)
# Craft an MQTT PUBLISH packet to send a message
topic = "sensor/data"
MAX_SIZE = 60 * 1024  # 60 KB
message = "A" * MAX_SIZE
publish_pkt = create_publish_packet(topic, message)
# Loop for TCP connection, MQTT connection, sending packets, and disconnecting
for i in range(number_packets):
    # publish_pkt.show()
    message_id = i # Generate a unique message ID for each message
    publish_pkt = MQTT(QOS=2)/MQTTPublish(topic=topic, value=message, msgid=message_id)
    send(ip/TCP(sport=src_port, dport=broker_port, flags="PA", seq=seq, ack=ack.ack)/publish_pkt)
    seq += len(publish_pkt) # +1 for the ACK?
    time.sleep(0.01)


# Craft an MQTT DISCONNECT packet to close the session
disconnect_pkt = MQTT()/MQTTDisconnect()
send(ip/TCP(sport=src_port, dport=broker_port, flags="PA", seq=seq, ack=ack.ack)/disconnect_pkt)
close_tcp_connection(ip, src_port, broker_port, seq, ack)




