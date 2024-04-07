# Missing SEQ and ACK numbers
# Might implement with wireshark

from scapy.all import *

def craft_mqtt_publish(topic, message, qos=0):
    """
    Craft an MQTT PUBLISH packet with the specified topic, message, and QoS level.
    
    :param topic: Topic to publish the message to.
    :param message: Message to publish.
    :param qos: Quality of Service level (0, 1, or 2).
    :return: Crafted MQTT PUBLISH packet.
    """
    # MQTT PUBLISH Fixed Header
    # Type: PUBLISH (0011), Flags: DUP=0, QoS=[qos], RETAIN=0
    mqtt_type_and_flags = 0x30 | ((qos & 0x03) << 1)
    remaining_length = 2 + len(topic) + len(message)  # Topic length (2 bytes) + topic + message
    
    # MQTT PUBLISH Variable Header
    topic_length_bytes = struct.pack("!H", len(topic))  # Topic length (2 bytes, big-endian)
    variable_header = topic_length_bytes + bytes(topic, 'utf-8')
    
    # Payload
    payload = bytes(message, 'utf-8')
    
    # MQTT PUBLISH packet
    mqtt_publish_packet = Raw(load=bytes([mqtt_type_and_flags, remaining_length]) + variable_header + payload)
    
    return mqtt_publish_packet

# Example usage
topic = "sensor/data"
message = "Hijacked mqtt"
mqtt_packet = craft_mqtt_publish(topic, message, qos=0)

# Example of sending the packet would go here
# send(ip/tcp/mqtt_packet)

print("MQTT PUBLISH packet crafted.")
