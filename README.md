
read displayport of Votronic MP430 Duo Digital Solar Regulator and output as json

```sh
$ votronic | head -n1 | jq
```

```json
{
  "model_id": "0x1a",
  "V_bat": 13.03,
  "V_solar": 17.7,
  "I_charge": 3.4,
  "P_charge": 44.302,
  "ctrl_temp": 34,
  "bat_status": "i_phase",
  "ctrl_status": [
    "active",
    "mppt"
  ],
  "charge_mode": "lead_agm1",
  "datagram": "aa1a1705ea06220000000022220009cf",
  "timestamp": "2022-10-29 11:52:52.395131"
}
```

# Pinout
```
 .------------------.
 |                  |    Front view
 |                  |    into 6P6C socket
 |                  |
 | .  .  .  .  .  . |
 '-+--+--+--+--+--+-'
   1  2  3  4  5  6
   |  |     |
   |  |     |
   |  |     +- GND
   |  +------- 5V+ Vcc
   +---------- DAT (via level shifter to RX pin on pi)

```
# Raspberry Pi
* use level shifter (5V -> 3.3V)
* add ```enable_uart=1``` to /boot/config.txt
* ensure serial console is disabled
  * use ```console=tty``` in /boot/cmdline.txt not ```console=/dev/ttyAMA0``` etc.
  * remove ```agetty``` entries for serial port (/dev/tty/AMA0) from inittab/systemd

# Setup

Use pip to install:

```sh
$ git clone https://github.com/heeplr/votronic
$ pip install --user votronic
```

or similar

# Usage

```sh
$ votronic -h
Usage: votronic [OPTIONS]

  read displayport of Votronic MP430 Duo Digital Solar Regulator and output as
  json

Options:
  -p, --port TEXT                 serial port  [env var: VOTRONIC_PORT;
                                  default: /dev/ttyAMA0]
  -b, --baudrate INTEGER          serial baudrate  [env var:
                                  VOTRONIC_BAUDRATE; default: 1020]
  -D, --dump / -P, --parse        parse datagrams or just dump for debugging
                                  [env var: VOTRONIC_DUMP; default: parse]
  -e, --exclude [model_id|V_bat|V_solar|I_charge|P_charge|ctrl_temp|bat_status|ctrl_status|charge_mode|datagram|timestamp]
                                  exclude those fields in output (repeat for
                                  multiple fields)  [env var:
                                  VOTRONIC_EXCLUDE]
  -h, --help                      Show this message and exit.
```

## Throttled log to JSON file

Only log every 50th datagram to file:

```sh
$ votronic | gawk 'NR==1 || NR%50 == 0 { print; fflush(); }' >> votronic-solar.json
```


# References

* [crathje/VotronicSRDuoDig](https://github.com/crathje/VotronicSRDuoDig) uses ESP32
* [SirReal's Raspberry on a boat #16](https://youtu.be/tXYK4e92x7Q) uses NodeRed
* [scy/votonic](https://codeberg.org/scy/votonic) reads RS485 bus from votronic battery charger and inverter
* [cumulumbus blog](https://cumulumbus.de/smart-camper-auslesen-der-batterie-und-solarinformationen-aus-dem-votronic-bluetooth-connector/) uses votronic bluetooth connector
