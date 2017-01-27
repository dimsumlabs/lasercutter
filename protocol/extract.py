#!/usr/bin/env python
#
#

import sys
import pcap

def packet_handler(datalen, data, timestamp):
    if len(data)>0x41 and data[0x40]=='\xa6':
        print data[0x42:]

def main():
    p = pcap.pcapObject()
    filename = sys.argv[1]

    p.open_offline(filename)
    p.dispatch(-1,packet_handler)


if __name__=='__main__':
    main()

