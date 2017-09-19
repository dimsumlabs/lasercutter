#!/usr/bin/env python
#
#

import sys
import pcap # debian package python-libpcap (not the other python 'pcap' lib)

timestamp_first = None

# Some status bit definitions, taken from a CH341 driver - they may or may
# not be relevant
# / Bit 7 - Bit 0 corresponds to the D7-D0 pin of CH341
# / Bit 8 corresponds to the ERR # pin of CH341
# / bit 9 corresponds to the PEMP pin of CH341
# / bit 10 corresponds to the INT # pin of CH341
# / bit 11 corresponds to the SLCT pin of CH341
# / Bit 13 corresponds to the BUSY / WAIT # pin of CH341
# / bit 14 corresponds to the AUTOFD # / DATAS # pin of CH341
# / bit 15 corresponds to the SLCTIN # / ADDRS # pin of CH341
# / bit 23 corresponds to the SDA pin of CH341

# This python CRC function taken from http://www.scorchworks.com/K40whisperer
#######################################################################
#  The one wire CRC algorithm is derived from the OneWire.cpp Library
#  The latest version of this library may be found at:
#  http://www.pjrc.com/teensy/td_libs_OneWire.html
#######################################################################
def OneWireCRC(line):
    crc=0
    for i in range(len(line)):
        inbyte=ord(line[i])
        for j in range(8):
            mix = (crc ^ inbyte) & 0x01
            crc >>= 1
            if (mix):
                crc ^= 0x8C
            inbyte >>= 1
    return crc

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

    description = ''
    comment = ''
    # default to just displaying the whole "leftover capture data"
    databuf = data[0x40:]

    # output data packets
    if urb_type=='S' and transfer_type=='URB_BULK' and direction=='>':
        opcodes = {
            '\xa0': 'CMD_GETSTATUS',    # mCH341_PARA_CMD_STS
            '\xa6': 'CMD_SENDDATA',     # mCH341_PARA_CMD_W0
        }
        description = opcodes[data[0x40]]
        databuf = data[0x41:]

        if len(databuf) >0:
            mbz_buf = ord(databuf[0])
            crc_buf = ord(databuf[-1])
            databuf = databuf[1:-2]

            if mbz_buf != 0:
                comment += "ERROR: MBZ={:x} ".format(mbz_buf)

            crc_calc = OneWireCRC(databuf)

            if crc_buf != crc_calc:
                comment += "ERROR: CRC={:x}, calc={:x}".format(crc_buf,crc_calc)

    # The only inputs I have seen appears to be status replies
    if urb_type=='C' and transfer_type=='URB_BULK' and direction=='<':
        seen_status = {
            '\xff\xcc\x5f\x08\x13\x00': 'postinit1', # occurs occasionally
            '\xff\xcc\x6f\x08\x13\x00': 'postinit ',  # seen after first init string sent
            '\xff\xce\x4f\x08\x13\x00': 'idle3    ',     # occurs occasionally
            '\xff\xce\x5f\x08\x13\x00': 'idle2    ',     # occurs occasionally
            '\xff\xce\x6f\x08\x13\x00': 'idle1    ',     # seen before the plot starts (idle?)
            '\xff\xce\x7f\x08\x13\x00': 'idle4    ',     # occurs occasionally
            '\xff\xec\x6f\x08\x13\x00': 'idle5    ',     # occurs occasionally
            '\xff\xee\x4f\x08\x13\x00': 'pause3   ',    # occurs occasionally
            '\xff\xee\x5f\x08\x13\x00': 'pause2   ',    # occurs occasionally
            '\xff\xee\x6f\x08\x13\x00': 'pause1   ',    # perhaps a busy signal
            '\xff\xee\x7f\x08\x13\x00': 'pause4   ',    # occurs occasionally
        }
        description = '       STATUS='+seen_status[data[0x40:]]
        databuf = ' '.join(map("{0:b}".format, map(ord,list(databuf))))

    if show_packet:
        print "{:7.2f} {} {} {}: {} {}".format(
            timestamp_delta,
            transfer_type,
            direction,
            description,
            databuf,
            comment,
        )

def main():
    p = pcap.pcapObject()
    filename = sys.argv[1]

    p.open_offline(filename)
    p.dispatch(-1,packet_handler)


if __name__=='__main__':
    main()

