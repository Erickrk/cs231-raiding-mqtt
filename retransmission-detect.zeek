event tcp_packet(c: connection, is_orig: bool, flags: string, seq: count, ack: count, len: count, payload: string)
{
        if (c$tcp$in_retransmit >= 10)
        {
            print fmt("10 TCP retransmission errors detected in connection %s", c$id$orig_h);
        }
}