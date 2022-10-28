#!/usr/bin/env python3

"""read displayport of Votronic MP430 Duo Digital Solar Regulator and output as json"""

import click
import json
import asyncio
import serial_asyncio

from votronic import VotronicProtocol


# ----------------------------------------------------------------------
@click.command(
    context_settings={
        "help_option_names": ["-h", "--help"],
        "auto_envvar_prefix": "VOTRONIC",
    }
)
@click.option(
    "--port",
    "-p",
    default="/dev/ttyAMA0",
    show_default=True,
    show_envvar=True,
    help="serial port",
)
@click.option(
    "--baudrate",
    "-b",
    default=1020,
    show_default=True,
    show_envvar=True,
    help="serial baudrate",
)
@click.option(
    "--dump/--parse",
    "-D/-P",
    default=False,
    show_default=True,
    show_envvar=True,
    help="parse datagrams or just dump for debugging",
)
@click.option(
    "--exclude",
    "-e",
    type=click.Choice(VotronicProtocol.parsed_datagram.keys(), case_sensitive=False),
    default=[],
    multiple=True,
    show_default=True,
    show_envvar=True,
    help="exclude those fields in output (repeat for multiple fields)",
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


if __name__ == "__main__":
    read_votronic()
