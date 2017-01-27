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

    comment = ''
    # default to just displaying the whole "leftover capture data"
    databuf = data[0x40:]

    # output data packets
    if urb_type=='S' and transfer_type=='URB_BULK' and direction=='>':
        opcodes = {
            '\xa0': 'CMD_GETSTATUS',    # mCH341_PARA_CMD_STS
            '\xa6': 'CMD_SENDDATA',     # mCH341_PARA_CMD_W0
        }
        comment = opcodes[data[0x40]]
        databuf = data[0x41:]

    # The only inputs I have seen appears to be status replies
    if urb_type=='C' and transfer_type=='URB_BULK' and direction=='<':
        seen_status = {
            '\xff\xcc\x5f\x08\x13\x00': 'STATUS=postinit1', # occurs occasionally
            '\xff\xcc\x6f\x08\x13\x00': 'STATUS=postinit',  # seen after first init string sent
            '\xff\xce\x4f\x08\x13\x00': 'STATUS=idle3',     # occurs occasionally
            '\xff\xce\x5f\x08\x13\x00': 'STATUS=idle2',     # occurs occasionally
            '\xff\xce\x6f\x08\x13\x00': 'STATUS=idle1',     # seen before the plot starts (idle?)
            '\xff\xce\x7f\x08\x13\x00': 'STATUS=idle4',     # occurs occasionally
            '\xff\xec\x6f\x08\x13\x00': 'STATUS=idle5',     # occurs occasionally
            '\xff\xee\x4f\x08\x13\x00': 'STATUS=pause3',    # occurs occasionally
            '\xff\xee\x5f\x08\x13\x00': 'STATUS=pause2',    # occurs occasionally
            '\xff\xee\x6f\x08\x13\x00': 'STATUS=pause1',    # perhaps a busy signal
            '\xff\xee\x7f\x08\x13\x00': 'STATUS=pause4',    # occurs occasionally
        }
        comment = '       '+seen_status[data[0x40:]]

    if show_packet:
        print "{:7.2f} {} {} {}: {}".format(
            timestamp_delta,
            transfer_type,
            direction,
            comment,
            databuf
        )

def main():
    p = pcap.pcapObject()
    filename = sys.argv[1]

    p.open_offline(filename)
    p.dispatch(-1,packet_handler)


if __name__=='__main__':
    main()

