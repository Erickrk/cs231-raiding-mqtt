from scapy.all import *
from scapy.layers.inet import IP, TCP
from scapy.contrib.mqtt import *
import random
import threading

broker_ip = "192.168.122.48"
broker_port = 1883
number_packets = 20000

# MQTT Connect Packet for version 3.1.1
def create_connect_packet(client_id=""):
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
    payload = struct.pack("!H4s", client_id_length, client_id.encode())

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


def mqtt_publish(src_port):
    # Generate a unique client ID for each connection
    client_id = "".join(random.choices(string.ascii_uppercase + string.digits, k=4))

    # Establish a TCP connection (SYN, SYN+ACK, ACK)
    syn = TCP(sport=src_port, dport=broker_port, flags='S', seq=RandInt())
    syn_ack = sr1(ip/syn)
    ack = TCP(sport=src_port, dport=broker_port, flags='A', seq=syn_ack.ack, ack=syn_ack.seq + 1)
    send(ip/ack)

    # Now that the TCP connection is established, we can send MQTT packets
    # Craft an MQTT CONNECT packet with the unique client ID
    connect_pkt = create_connect_packet(client_id=client_id)
    send(ip/TCP(sport=src_port, dport=broker_port, flags="PA", seq=ack.seq, ack=ack.ack)/connect_pkt)

    # Wait a bit for the broker to process our connection
    time.sleep(2)

    # Craft an MQTT PUBLISH packet to send a message
    topic = "sensor/data"
    MAX_SIZE = 60 * 1024  # 60 KB
    message = "A" * MAX_SIZE
    publish_pkt = create_publish_packet(topic=topic, message="message")
    send(ip/TCP(sport=src_port, dport=broker_port, flags="PA", seq=ack.seq, ack=ack.ack)/publish_pkt)

# Generate a list of random source ports
src_ports = [random.randint(0, 0xFFFF) for _ in range(10)]  # Adjust the range as needed

# Start a thread for each source port
threads = []
for src_port in src_ports:
    t = threading.Thread(target=mqtt_publish, args=(src_port,))
    t.start()
    threads.append(t)

# Wait for all threads to finish
for t in threads:
    t.join()