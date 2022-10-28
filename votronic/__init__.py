"""read displayport of Votronic MP430 Duo Digital Solar Regulator"""


import asyncio
from dataclasses import asdict, dataclass
import datetime
import struct
import serial_asyncio


@dataclass
class VotronicDatagram:
    # id byte
    model_id: int = None
    # Volt
    V_bat: float = None
    # Volt
    V_solar: float = None
    # Ampere
    I_charge: float = None
    # V_bat * I_charge
    P_charge: float
    # ?
    ctrl_temp: int = None
    # bitfield
    bat_status: str = None
    # bitfield
    ctrl_status: list = None
    charge_mode: str = None
    datagram: str = None
    timestamp: str = None

    @property
    def P_charge(self):
        return self.I_charge * self.V_bat

    @P_charge.setter
    def P_charge(self, value):
        return

class VotronicProtocol(asyncio.Protocol):
    """read from serial, extract datagram, parse, pass dataclass"""
    # size of one datagram in bytes
    DATAGRAM_SIZE = 16
    # True if we shouldn't parse but just dump datagrams for debugging
    DUMP = False
    # exclude those fields in parsed datagram output
    EXCLUDE = []
    # callback for received datagrams
    CALLBACK = None
    # queue for incoming raw serial data
    queue = b""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # initialize datagram object
        self.datagram = VotronicDatagram()

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
            if len(self.queue) >= self.DATAGRAM_SIZE + preamble:
                # separate our datagram from datagram stream
                datagram = self.queue[preamble : self.DATAGRAM_SIZE + preamble]

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
                if parsed_datagram := parser(datagram):
                    self.CALLBACK(parsed_datagram)

                # remove datagram from queue and seek to start of next datagram
                self.queue = self.queue[self.DATAGRAM_SIZE + preamble :]

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
            solar_voltage,
            charge_current,
            flags1,
            flags2,
            flags3,
            controller_temp,
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
            # charge current * 10 (signed short)
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
            0: "i_phase",
            1: "u1_phase",
            2: "u2_phase",
            3: "u3_phase",
        }
        bat_status = bat_status_bits[int(bat_status & 0b00001111)]

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

        # decoded datagram
        self.datagram.model_id = hex(model)
        self.datagram.V_bat = bat_voltage / 100
        self.datagram.V_solar = solar_voltage / 100
        self.datagram.I_charge = charge_current / 10
        self.datagram.ctrl_temp = controller_temp
        self.datagram.bat_status = bat_status
        self.datagram.ctrl_status = controller_status
        self.datagram.charge_mode = charge_mode
        self.datagram.datagram = datagram.hex()
        self.datagram.timestamp = str(datetime.datetime.now())

        return self.datagram

    def crc(self, datagram):
        """True if valid CRC, False otherwise"""
        b = b"\x00"
        for c in datagram[1:]:
            b ^= c
        return b == 0
