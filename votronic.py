"""read displayport of Votronic MP430 Duo Digital Solar Regulator"""


import asyncio
import struct
import serial_asyncio


DATAGRAM_SIZE = 16


class VotronicProtocol(asyncio.Protocol):
    """read from serial, extract datagram, parse, output as JSON"""

    # True if we shouldn't parse but just dump datagrams for debugging
    DUMP = False
    # exclude those fields in parsed datagram output
    EXCLUDE = []
    # queue for incoming raw serial data
    queue = b""
    # skeleton for our parsed datagram (@todo this should be a dataclass)
    parsed_datagram = {
        "model_id": None,
        "V_bat": None,
        "V_solar": None,
        "I_charge": None,
        "temp": None,
        "bat_status": None,
        "ctrl_status": None,
        "charge_mode": None,
        "datagram": None,
    }

    def connection_made(self, transport):
        """called after serial port initialization"""
        self.transport = transport

    def data_received(self, data):
        """called when serial data is received"""
        # append to already received datagrams
        self.queue += data

        # get position of preamble for all preambles
        # while preamble := self.datagrams.find(b'\xAA') > 0:
        while True:
            preamble = self.queue.find(b"\xAA")
            if preamble < 0:
                # wait for more data
                break

            # got complete datagram?
            if len(self.queue) >= DATAGRAM_SIZE + preamble:
                # separate our datagram from datagram stream
                datagram = self.queue[preamble : DATAGRAM_SIZE + preamble]
                # dump only?
                if self.DUMP:
                    print(datagram.hex())

                # parse datagram
                else:
                    # choose datagram parser by model id
                    MODELS = {
                        0xAA: self.parse_mpxxx
                    }

                    # select parser from model ID (2nd byte of datagram)
                    model = datagram[1]
                    try:
                        parser = MODELS[model]
                    except KeyError:
                        # no parser found, try default
                        parser = MODELS[0xAA]

                    # output parsed datagram (if valid)
                    # if result := parser(datagram):
                    result = parser(datagram)
                    if result:
                        # remove excluded keys from result
                        result = {
                            k: v for k, v in result.items() if k not in self.EXCLUDE
                        }
                        # output
                        print(json.dumps(result))

                # remove datagram from queue and seek to start of next datagram
                self.queue = self.queue[DATAGRAM_SIZE + preamble :]

            # not enough data received, yet
            else:
                break

    def connection_lost(self, exc):
        """called after port close"""
        self.transport.loop.stop()

    def parse_mpxxx(self, datagram):
        """parse single datagram to json serializable dict"""

        # unpack datagram
        (
            model,
            bat_voltage,
            solar_current,
            charge_current,
            flags1,
            flags2,
            flags3,
            temperature,
            charge_mode,
            bat_status,
            controller_status,
            checksum,
        ) = struct.unpack_from(
            # use little endian mode
            "<"
            # model ID (char)
            "b"
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
            # battery status flags (char)
            "b"
            # controller status flags (char)
            "b"
            # checksum
            "c",
            buffer=datagram,
            # skip first byte (preamble)
            offset=1,
        )

        # look up charge mode
        charge_modes = {
            0x35: "lead_gel",
            0x22: "lead_agm1",
            0x2F: "lead_agm2",
            0x50: "lifepo4_13.9V",
            0x52: "lifepo4_14.2V",
            0x54: "lifepo4_14.4V",
            0x56: "lifepo4_14.6V",
            0x58: "lifepo4_14.8V",
        }
        try:
            charge_mode = charge_modes[int(charge_mode & 0b01111111)]
        except KeyError:
            charge_mode = f"unknown: {charge_mode}"

        # read battery status bits
        bat_status_bits = {
            0b00000001: "i_phase",
            0b00000010: "u1_phase",
            0b00000100: "u2_phase",
            0b00001000: "u3_phase",
        }
        bat_status = [
            status for bit, status in bat_status_bits.items() if bit & bat_status
        ]

        # read controller status bits
        controller_status_bits = {
            0b10000000: "unknown8",
            0b01000000: "unknown7",
            0b00100000: "unknown6",
            0b00010000: "charged_over80percent",
            0b00001000: "unknown4",
            0b00000100: "unknown3",
            0b00000010: "unknown2",
            0b00000001: "unknown1"
        }
        controller_status = [
            status
            for bit, status in controller_status_bits.items()
            if bit & controller_status
        ]

        # decoded datagram dict
        self.parsed_datagram = {
            "model_id": hex(model),
            "V_bat": bat_voltage / 100,
            "V_solar": solar_current / 100,
            "I_charge": charge_current / 100,
            "temp": temperature,
            "bat_status": bat_status,
            "ctrl_status": controller_status,
            "charge_mode": charge_mode,
            "datagram": datagram.hex(),
        }
        return self.parsed_datagram

    def crc(self, datagram):
        """True if valid CRC, False otherwise"""
        b = b"\x00"
        for c in datagram[1:]:
            b ^= c
        return b == 0
