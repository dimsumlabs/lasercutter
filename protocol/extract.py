#!/usr/bin/env python
#
#

import sys
import pcap

timestamp_first = None

def packet_handler(datalen, data, timestamp):
    global timestamp_first
    if timestamp_first is None:
        timestamp_first = timestamp

    timestamp_delta = timestamp - timestamp_first

    transfer_types = {
        '\x02': 'URB_CONTROL',
        '\x03': 'URB_BULK',
    }
    urb_type = data[8]
    transfer_type = transfer_types[data[9]]
    if ord(data[10]) & 0x80:
        direction = "<"
    else:
        direction = ">"

    # Hide packets that are basically noise
    # - USB sends an empty setup packet for every reply packet
    # - and an empty complete packet ACK for every transmit
    
    show_packet = True
    if urb_type=='S' and transfer_type=='URB_BULK' and direction=='<':
        show_packet = False
    if urb_type=='C' and transfer_type=='URB_BULK' and direction=='>':
        show_packet = False

    if show_packet:
        print "{:7.2f} {} {} {}".format(
            timestamp_delta,
            transfer_type,
            direction,
            data[0x40:]
        )

def main():
    p = pcap.pcapObject()
    filename = sys.argv[1]

    p.open_offline(filename)
    p.dispatch(-1,packet_handler)


if __name__=='__main__':
    main()

