"""
Automatically finds a compatible device (Photon, Core, Arduino), modified from Matthews work in brewpi-connector
"""

from __future__ import absolute_import
from serial.tools import list_ports

known_devices = [
    {'vid': 0x2341, 'pid': 0x0010, 'name': "Arduino Mega2560"},
    {'vid': 0x2341, 'pid': 0x8036, 'name': "Arduino Leonardo"},
    {'vid': 0x2341, 'pid': 0x0036, 'name': "Arduino Leonardo Bootloader"},
    {'vid': 0x2341, 'pid': 0x0043, 'name': "Arduino Uno"},
    {'vid': 0x2341, 'pid': 0x0001, 'name': "Arduino Uno"},
    {'vid': 0x2a03, 'pid': 0x0010, 'name': "Arduino Mega2560"},
    {'vid': 0x2a03, 'pid': 0x8036, 'name': "Arduino Leonardo"},
    {'vid': 0x2a03, 'pid': 0x0036, 'name': "Arduino Leonardo Bootloader"},
    {'vid': 0x2a03, 'pid': 0x0043, 'name': "Arduino Uno"},
    {'vid': 0x2a03, 'pid': 0x0001, 'name': "Arduino Uno"},
    {'vid': 0x1D50, 'pid': 0x607D, 'name': "Particle Core"},
    {'vid': 0x2B04, 'pid': 0xC006, 'name': "Particle Photon"},
    {'vid': 0x2B04, 'pid': 0xC008, 'name': "Particle P1"}
]


def recognized_device_name(device):
    if device is not None:
        for known in known_devices:
            if device.vid == known['vid'] and device.pid == known['pid']: # match on VID, PID
                return known['name']
    return None

def find_compatible_serial_ports(bootLoader = False):
    ports = find_all_serial_ports()
    for p in ports:
        name = recognized_device_name(p)
        if name is not None:
            if "Bootloader" in name and not bootLoader:
                continue
            yield p


def find_all_serial_ports():
    """
    :return: a list of serial port info tuples
    :rtype:
    """
    all_ports = list_ports.comports()
    return iter(all_ports)


def detect_port(bootLoader = False):
    """
    :return: first detected serial port as tuple: (port, name)
    :rtype:
    """
    port = None
    ports = find_compatible_serial_ports(bootLoader=bootLoader)
    try:
        port = ports.next()
    except StopIteration:
        return port
    try:
        another_port = ports.next()
        print "Warning: detected multiple compatible serial ports, using the first."
    except StopIteration:
        pass
    return port


def find_port(identifier):
    p = None
    if 'socket://' in identifier:
        return { 'device': identifier, 'name': 'WiFi Spark', 'serial_number': 'unknown' }
    if identifier == 'auto':
        p = detect_port()
        if p is not None:
            name = recognized_device_name(p)
            if name is not None and 'Arduino' in name:
                print "This version of BrewPi is not compatible with Arduino. Please check out the legacy branch instead."
                return None
    for p in find_compatible_serial_ports():
        if p.serial_number == identifier or p.device == identifier or p.name == identifier :
            break
    if p is not None:
        return { 'device': p.device, 'name': p.name or p.device, 'serial_number': p.serial_number, 'product': p.product or recognized_device_name(p)}


def find_serial_numbers():
    serial_numbers = []
    for p in find_compatible_serial_ports():
        if p.serial_number:
            serial_numbers.append(p.serial_number)
    return serial_numbers


if __name__ == '__main__':
    print "All ports:"
    for p in find_all_serial_ports():
        try:
            print "{0}, VID:{1:04x}, PID:{2:04x}, SER:{3}".format(str(p), p.vid, p.pid, p.serial_number)
        except ValueError:
            # could not convert pid and vid to hex
            print "{0}, VID:{1}, PID:{2}".format(str(p), (p.vid), (p.pid))
    print "Compatible ports: "
    for p in find_compatible_serial_ports():
        print p

    print "\nChosen for 2f0031000547343232363230"
    print(find_port("2f0031000547343232363230"))
    print "\nChosen for ttyACM0"
    print(find_port("ttyACM0"))
    print "\nChosen for /dev/ttyACM0:"
    print(find_port("/dev/ttyACM0"))
    print "\nChosen for auto:"
    print(find_port("auto"))
    print "\nChosen for socket://192.168.1.100:6666"
    print(find_port("socket://192.168.1.100:6666"))
    print "\nChosen for wrong_port:"
    print(find_port("wrong_port"))

    print "\nAll compatible serial numbers"
    print find_serial_numbers()
