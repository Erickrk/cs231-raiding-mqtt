module MQTT;

export {
    ## Tracks MQTT QoS 2 messages from each host
    global host_mqtt_qos2: table[addr] of count &create_expire=5min &default=0;

    ## Event that triggers when MQTT message is observed
    event mqtt_message_seen(c: connection, qos: count) {
        # Check for QoS 2 messages
        if (qos == 2) {
            host_mqtt_qos2[c$id$orig_h] += 1;

            # Check if the count exceeds the threshold
            if (host_mqtt_qos2[c$id$orig_h] > 20) {
                print fmt("Possible MQTT DoS attack detected from %s", c$id$orig_h);
                # Reset the counter after the alert
                host_mqtt_qos2[c$id$orig_h] = 0;
            }
        }
    }
}

event zeek_init() &priority=5 {
    # Initialize global variables
    host_mqtt_qos2 = table();
}

event zeek_done() &priority=-5 {
    # Clean up global variables
    # delete host_mqtt_qos2;
}
