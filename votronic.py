#!/usr/bin/env python3

"""read displayport of Votronic MP430 Duo Digital Solar Regulator and output as json"""


import asyncio
import json
import struct
import sys
import click
import serial_asyncio


DATAGRAM_SIZE = 16


class VotronicProtocol(asyncio.Protocol):
    """read from serial, extract datagram, parse, output as JSON"""

    # True if we shouldn't parse but just dump datagrams for debugging
    DUMP = False
    # exclude those fields in parsed datagram output
    EXCLUDE = []
    # queue for incoming raw serial data
    queue = b''
    # skeleton for our parsed datagram
    parsed_datagram = {
        'id': None,
        'V_bat': None,
        'V_solar': None,
        'I_charge': None,
        'mode': None,
        'temp': None,
        'flags': None,
        'checksum': None
    }

    def connection_made(self, transport):
        self.transport = transport

    def data_received(self, data):
        # append to already received datagrams
        self.queue += data

        # get position of preamble for all preambles
        #while preamble := self.datagrams.find(b'\xAA') > 0:
        preamble = 0
        while True:
            preamble = self.queue.find(b'\xAA')
            if preamble < 0:
                break

            # got complete datagram?
            if len(self.queue) >= DATAGRAM_SIZE + preamble:
                # separate our datagram from datagram stream
                datagram = self.queue[preamble:DATAGRAM_SIZE + preamble]
                # dump only?
                if self.DUMP:
                    print(datagram.hex())
                else:
                    # output parsed datagram (if valid)
                    #if result := self.parse_datagram(datagram):
                    result = self.parse_datagram(datagram)
                    if result:
                        # remove excluded keys from result
                        result = { k:v for k,v in result.items() if k not in self.EXCLUDE }
                        # output
                        print(json.dumps(result))

                # remove datagram from queue and seek to start of next datagram
                self.queue = self.queue[DATAGRAM_SIZE + preamble:]

            # not enough data received, yet
            else:
                break

    def connection_lost(self, exc):
        self.transport.loop.stop()

    def pause_writing(self):
        print(self.transport.get_write_buffer_size())

    def resume_writing(self):
        print(self.transport.get_write_buffer_size())

    def parse_datagram(self, datagram):
        """parse single datagram to json serializable dict"""

        charge_modes = {
            0x35: "lead_gel",
            0x22: "lead_agm1",
            0x2f: "lead_agm2",
            0x50: "lifepo4_13.9V",
            0x52: "lifepo4_14.2V",
            0x54: "lifepo4_14.4V",
            0x56: "lifepo4_14.6V",
            0x58: "lifepo4_14.8V"
        }

        # unpack datagram (skip first byte, is preamble)
        model, bat_voltage, solar_current, charge_current, flags1, flags2, flags3, \
        temperature, charge_mode, flags4, flags5, checksum = struct.unpack_from(
            # use little endian mode
            "<"
            # model ID (char)
            "c"
            # battery voltage * 100 (signed short)
            "h"
            # solar input voltage * 100 (signed short)
            "h"
            # charge current * 100 (signed short)
            "h"
            # flags (3x char)
            "3b"
            # temperature degree celsius (signed char)
            "b"
            # charge mode/battery type (char)
            "B"
            # flags (2x char)
            "2b"
            # checksum
            "c",
        buffer=datagram,
        offset=1)

        # extract unused bit from charge_mode, in case it's used
        flag = charge_mode & 0b10000000

        # maybe battery full ?
        charge_full = bool(flags4 & 0b1)
        # erase bit from flags
        flags4 &= 0b11111110
        # maybe >80% ?
        charge_over80percent = bool(flags5 & 0b10000)
        # erase bit from flags
        flags5 &= 0b01111
        # mask upper bit from charge_mode (just to be sure)
        charge_mode &= 0b01111111
        # look up charge mode
        try:
            charge_mode = charge_modes[int(charge_mode)]
        except KeyError:
            charge_mode = f"unknown: {charge_mode}"

        self.parsed_datagram = {
            'model': model.hex(),
            'V_bat': bat_voltage/100,
            'V_solar': solar_current/100,
            'I_charge': charge_current/100,
            'temp': temperature,
            'charge_mode': charge_mode,
            'charge_full': charge_full,
            'charge_over80': charge_over80percent,
            'flags': [ hex(flags1), hex(flags2), hex(flags3), hex(flags4), hex(flags5), hex(flag) ],
            'checksum': checksum.hex()
        }
        return self.parsed_datagram

    def crc(self, datagram):
        """True if valid CRC, False otherwise"""
        b = b'\x00'
        for c in datagram[1:]:
            b ^= c;
        return b == 0


# ----------------------------------------------------------------------
@click.command(context_settings={
    "help_option_names": ['-h', '--help'],
    "auto_envvar_prefix": "VOTRONIC"
})
@click.option('--port', '-p',
    default="/dev/ttyS0",
    show_default=True,
    show_envvar=True,
    help="serial port"
)
@click.option('--baudrate', '-b',
    default=1020,
    show_default=True,
    show_envvar=True,
    help="baudrate"
)
@click.option('--dump/--parse', '-D/-P',
    default=False,
    show_default=True,
    show_envvar=True,
    help="parse datagrams or just dump for debugging"
)
@click.option('--exclude', '-e',
    type=click.Choice(VotronicProtocol.parsed_datagram.keys(), case_sensitive=False),
    default=[],
    multiple=True,
    show_default=True,
    show_envvar=True,
    help="exclude those fields in output"
)
def read_votronic(port, baudrate, dump, exclude):
    """read displayport of Votronic MP430 Duo Digital Solar Regulator and output as json"""

    # set protocol options
    VotronicProtocol.DUMP = dump
    VotronicProtocol.EXCLUDE = exclude

    # setup asyncio loop
    loop = asyncio.get_event_loop()
    coro = serial_asyncio.create_serial_connection(
        loop, VotronicProtocol, url=port, baudrate=baudrate
    )
    transport, protocol = loop.run_until_complete(coro)

    # fire!
    loop.run_forever()

    # cleanup
    loop.close()
    transport.close()


if __name__ == '__main__':
    read_votronic()
