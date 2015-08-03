"""
Automatically finds a compatible device (Photon, Core, Arduino), modified from Matthews work in brewpi-connector
"""

from __future__ import absolute_import
import re
from serial.tools import list_ports


def serial_ports():
    """
    Returns a generator for all available serial ports
    """
    for port in serial_port_info():
        yield port[0]

known_devices = {
    (r"USB VID\:PID=2341\:0010.*"): "Arduino Mega2560",
    (r"USB VID\:PID=2341\:8036.*"): "Arduino Leonardo",
    (r'USB VID:PID=2341:0043.*'): "Arduino Uno",
    (r"USB VID\:PID=1D50\:607D.*"): "Spark Core",
    (r"USB VID\:PID=2B04\:C006.*"): "Particle Photon",
}


def matches(text, regex):
    return re.match(regex, text)


def is_recognised_device(p):
    port, name, desc = p
    for d in known_devices.keys():
        if matches(desc.lower(), d.lower()): # match on VID
            return known_devices[d] # return name
    return None

def find_arduino_ports(ports):
    for p in ports:
        name = is_recognised_device(p)
        if name:
            yield (p[0], name)


def serial_port_info():
    """
    :return: a tuple of serial port info tuples,
    :rtype:
    """
    return tuple(list_ports.comports())


def detect_port():
    """
    :return: first detected serial port as tuple: (port, name)
    :rtype:
    """
    ports = detect_all_ports()
    if len(ports) > 1:
        print "Warning: detected multiple compatible serial ports, using the first."
    if ports:
        return ports[0]
    return (None, None)

def detect_all_ports():
    """
    :return: all compatible ports as list of tuples: (port, name)
    :rtype:
    """
    all_ports = serial_port_info()
    ports = tuple(find_arduino_ports(all_ports))
    return ports


def configure_serial_for_device(s, d):
    """ configures the serial connection for the given device.
    :param s the Serial instance to configure
    :param d the device (port, name, details) to configure the serial port
    """
    # for now, all devices connect at 57600 baud with defaults for parity/stop bits etc.
    s.setBaudrate(57600)


if __name__ == '__main__':
    print "All ports: ",  serial_port_info()
    print "Compatible ports: ", detect_all_ports()
    print "Selected port: ", detect_port()
