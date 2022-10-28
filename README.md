
read displayport of Votronic MP430 Duo Digital Solar Regulator and output as json

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

```
$ git clone https://github.com/heeplr/votronic
$ pip install --user votronic
```

or similar

# Usage

```
# votronic -h
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
