# Copyright 2012 BrewPi/Elco Jacobs.
# This file is part of BrewPi.

# BrewPi is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# BrewPi is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with BrewPi.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import print_function
import subprocess as sub
import serial
import time
import simplejson as json
import os
import brewpiVersion
import expandLogMessage
from distutils.version import LooseVersion
from MigrateSettings import MigrateSettings
from sys import stderr
import BrewPiUtil as util

# print everything in this file to stderr so it ends up in the correct log file for the web UI
def printStdErr(*objs):
    print("", *objs, file=stderr)

def asbyte(v):
    return chr(v & 0xFF)


class LightYModem:
    """
    Receive_Packet
    - first byte SOH/STX (for 128/1024 byte size packets)
    - EOT (end)
    - CA CA abort
    - ABORT1 or ABORT2 is abort

    Then 2 bytes for seqno (although the sequence number isn't checked)

    Then the packet data

    Then CRC16?

    First packet sent is a filename packet:
    - zero-terminated filename
    - file size (ascii) followed by space?
    """

    packet_len = 1024
    stx = 2
    eot = 4
    ack = 6
    nak = 0x15
    ca =  0x18
    crc16 = 0x43
    abort1 = 0x41
    abort2 = 0x61

    def __init__(self):
        self.seq = None
        self.ymodem = None

    def _read_response(self):
        ch1 = ''
        while not ch1:
            ch1 = self.ymodem.read(1)
        ch1 = ord(ch1)
        if ch1==LightYModem.ack and self.seq==0:    # may send also a crc16
            ch2 = self.ymodem.read(1)
        elif ch1==LightYModem.ca:                   # cancel, always sent in pairs
            ch2 = self.ymodem.read(1)
        return ch1

    def _send_ymodem_packet(self, data):
        # pad string to 1024 chars
        data = data.ljust(LightYModem.packet_len)
        seqchr = asbyte(self.seq & 0xFF)
        seqchr_neg = asbyte((-self.seq-1) & 0xFF)
        crc16 = '\x00\x00'
        packet = asbyte(LightYModem.stx) + seqchr + seqchr_neg + data + crc16
        if len(packet)!=1029:
            raise Exception("packet length is wrong!")

        self.ymodem.write(packet)
        self.ymodem.flush()
        response = self._read_response()
        if response==LightYModem.ack:
            printStdErr("sent packet nr %d " % (self.seq))
            self.seq += 1
        return response

    def _send_close(self):
        self.ymodem.write(asbyte(LightYModem.eot))
        self.ymodem.flush()
        response = self._read_response()
        if response == LightYModem.ack:
            self.send_filename_header("", 0)
            self.ymodem.close()

    def send_packet(self, file, output):
        response = LightYModem.eot
        data = file.read(LightYModem.packet_len)
        if len(data):
            response = self._send_ymodem_packet(data)
        return response

    def send_filename_header(self, name, size):
        self.seq = 0
        packet = name + asbyte(0) + str(size) + ' '
        return self._send_ymodem_packet(packet)

    def transfer(self, file, ymodem, output):
        self.ymodem = ymodem
        """
        file: the file to transfer via ymodem
        ymodem: the ymodem endpoint (a file-like object supporting write)
        output: a stream for output messages
        """
        file.seek(0, os.SEEK_END)
        size = file.tell()
        file.seek(0, os.SEEK_SET)
        response = self.send_filename_header("binary", size)
        while response==LightYModem.ack:
            response = self.send_packet(file, output)

        file.close()
        if response==LightYModem.eot:
            self._send_close()

        return response


def fetchBoardSettings(boardsFile, boardType):
    boardSettings = {}
    for line in boardsFile:
        if line.startswith(boardType):
            setting = line.replace(boardType + '.', '', 1).strip()  # strip board name, period and \n
            [key, sign, val] = setting.rpartition('=')
            boardSettings[key] = val
    return boardSettings


def loadBoardsFile(arduinohome):
    return open(arduinohome + 'hardware/arduino/boards.txt', 'rb').readlines()


def openSerial(port, altport, baud, timeoutVal):
    # open serial port
    try:
        ser = serial.Serial(port, baud, timeout=timeoutVal)
        return [ser, port]
    except (OSError, serial.SerialException) as e:
        if altport:
            try:
                ser = serial.Serial(altport, baud, timeout=timeoutVal)
                return [ser, altport]
            except (OSError, serial.SerialException) as e:
                pass
        return [None, None]



def programController(config, boardType, hexFile, restoreWhat):
    programmer = SerialProgrammer.create(config, boardType)
    return programmer.program(hexFile, restoreWhat)


def json_decode_response(line):
    try:
        return json.loads(line[2:])
    except json.decoder.JSONDecodeError, e:
        printStdErr("JSON decode error: " + str(e))
        printStdErr("Line received was: " + line)

msg_map = { "a" : "Arduino" }

class SerialProgrammer:
    @staticmethod
    def create(config, boardType):
        if boardType=='spark-core':
            msg_map["a"] = "Spark Core"
            programmer = SparkProgrammer(config, boardType)
        else:
            msg_map["a"] = "Arduino"
            programmer = ArduinoProgrammer(config, boardType)
        return programmer

    def __init__(self, config):
        self.config = config
        self.restoreSettings = False
        self.restoreDevices = False
        self.ser = None
        self.port = None
        self.avrVersionNew = None
        self.avrVersionOld = None
        self.oldSettings = {}

    def program(self, hexFile, restoreWhat):
        printStdErr("****    %(a)s Program script started    ****" % msg_map)

        self.parse_restore_settings(restoreWhat)
        if not self.open_serial(self.config, 57600, 0.2):
            return 0

        self.delay_serial_open()

        # request all settings from board before programming
        printStdErr("Checking old version before programming.")
        if self.fetch_current_version():
            self.retrieve_settings_from_serial()
            self.save_settings_to_file()

        if not self.flash_file(hexFile):
            return 0

        printStdErr("Waiting for device to reset.")

        # reopen serial port
        retries = 30
        self.ser = None
        while retries and not self.ser:
            time.sleep(1)
            self.open_serial(self.config, 57600, 0.2)
            retries -= 1

        if not self.ser:
            printStdErr("Error opening serial port after programming. Program script will exit. Settings are not restored.")
            return False

        time.sleep(1)
        self.fetch_new_version()
        self.reset_settings(self.ser)

        printStdErr("Now checking which settings and devices can be restored...")
        if self.avrVersionNew is None:
            printStdErr(("Warning: Cannot receive version number from controller after programming. "
                         "\nSomething must have gone wrong. Restoring settings/devices settings failed.\n"))
            return 0

        if(LooseVersion(self.avrVersionOld.toString()) < LooseVersion('0.1')):
            printStdErr("Could not receive valid version number from old board, " +
                        "No settings/devices are restored.")
            return 0

        if self.restoreSettings:
            printStdErr("Trying to restore compatible settings from " +
                        self.avrVersionOld.toString() + " to " + self.avrVersionNew.toString())

            if(LooseVersion(self.avrVersionNew.toString()) < LooseVersion('0.2')):
                printStdErr("Sorry, settings can only be restored when updating to BrewPi 0.2.0 or higher")
                self.restoreSettings = False

        if self.restoreDevices:
            if(LooseVersion(self.avrVersionNew.toString()) < LooseVersion('0.2')):
                printStdErr("Sorry, devices can only be restored when updating to BrewPi 0.2.0 or higher")
                self.restoreSettings = False

        if self.restoreSettings:
            self.restore_settings()

        if self.restoreDevices:
            self.restore_devices()

        printStdErr("****    Program script done!    ****")
        printStdErr("If you started the program script from the web interface, BrewPi will restart automatically")
        self.ser.close()
        self.ser = None
        return 1

    def parse_restore_settings(self, restoreWhat):
        restoreSettings = False
        restoreDevices = False
        if 'settings' in restoreWhat:
            if restoreWhat['settings']:
                restoreSettings = True
        if 'devices' in restoreWhat:
            if restoreWhat['devices']:
                restoreDevices = True
        # Even when restoreSettings and restoreDevices are set to True here,
        # they might be set to false due to version incompatibility later

        printStdErr("Settings will " + ("" if restoreSettings else "not ") + "be restored" +
                    (" if possible" if restoreSettings else ""))
        printStdErr("Devices will " + ("" if restoreDevices else "not ") + "be restored" +
                    (" if possible" if restoreSettings else ""))
        self.restoreSettings = restoreSettings
        self.restoreDevices = restoreDevices

    def open_serial(self, config, baud, timeout):
        self.ser = None
        self.ser, self.port = openSerial(config['port'], config.get('altport'), baud, timeout)
        if self.ser is None:
            return False
        return True

    def delay_serial_open(self):
        pass

    def fetch_version(self, msg):
        version = brewpiVersion.getVersionFromSerial(self.ser)
        if version is None:
            printStdErr(("Warning: Cannot receive version number from %(a)s. " % msg_map +
                         "Your %(a)s is either not programmed yet or running a very old version of BrewPi. "
                         "%(a)s will be reset to defaults."))
        else:
            printStdErr(msg+"Found " + version.toExtendedString() +
                        " on port " + self.port + "\n")
        return version

    def fetch_current_version(self):
        self.avrVersionOld = self.fetch_version("Checking current version: ")
        return self.avrVersionOld

    def fetch_new_version(self):
        self.avrVersionNew = self.fetch_version("Checking new version: ")
        return self.avrVersionNew

    def retrieve_settings_from_serial(self):
        ser = self.ser
        self.oldSettings.clear()
        printStdErr("Requesting old settings from %(a)s..." % msg_map)
        expected_responses = 2
        if not self.avrVersionOld.isNewer("2.0.0"):  # versions older than 2.0.0 did not have a device manager
            expected_responses += 1
            ser.write("d{}")  # installed devices
            time.sleep(1)
        ser.write("c")  # control constants
        ser.write("s")  # control settings
        time.sleep(2)

        while expected_responses:
            line = ser.readline()
            if line:
                line = util.asciiToUnicode(line)
                if line[0] == 'C':
                    expected_responses -= 1
                    self.oldSettings['controlConstants'] = json_decode_response(line)
                elif line[0] == 'S':
                    expected_responses -= 1
                    self.oldSettings['controlSettings'] = json_decode_response(line)
                elif line[0] == 'd':
                    expected_responses -= 1
                    self.oldSettings['installedDevices'] = json_decode_response(line)


    def save_settings_to_file(self):
        oldSettingsFileName = 'oldAvrSettings-' + time.strftime("%b-%d-%Y-%H-%M-%S") + '.json'
        scriptDir = util.scriptPath()  # <-- absolute dir the script is in
        if not os.path.exists(scriptDir + '/settings/avr-backup/'):
            os.makedirs(scriptDir + '/settings/avr-backup/')

        oldSettingsFile = open(scriptDir + '/settings/avr-backup/' + oldSettingsFileName, 'wb')
        oldSettingsFile.write(json.dumps(self.oldSettings))
        oldSettingsFile.truncate()
        oldSettingsFile.close()
        printStdErr("Saved old settings to file " + oldSettingsFileName)

    def delay(self, countDown):
        while countDown > 0:
            time.sleep(1)
            countDown -= 1
            printStdErr("Back up in " + str(countDown) + "...")

    def flash_file(self, hexFile):
        raise Exception("not implemented")

    def reset_settings(self, ser):
        printStdErr("Resetting EEPROM to default settings")
        ser.write('E')
        time.sleep(5)  # resetting EEPROM takes a while, wait 5 seconds
        line = ser.readline()
        if line:  # line available?
            if line[0] == 'D':
                # debug message received
                try:
                    expandedMessage = expandLogMessage.expandLogMessage(line[2:])
                    printStdErr(("%(a)s debug message: " % msg_map) + expandedMessage)
                except Exception, e:  # catch all exceptions, because out of date file could cause errors
                    printStdErr("Error while expanding log message: " + str(e))
                    printStdErr(("%(a)s debug message was: " % msg_map) + line[2:])

    def print_debug_log(self, line):
        try:  # debug message received
            expandedMessage = expandLogMessage.expandLogMessage(line[2:])
            printStdErr(expandedMessage)
        except Exception, e:  # catch all exceptions, because out of date file could cause errors
            printStdErr("Error while expanding log message: " + str(e))
            printStdErr(("%(a)s debug message: " % msg_map) + line[2:])

    def restore_settings(self):
        oldSettingsDict = self.get_combined_settings_dict(self.oldSettings)
        ms = MigrateSettings()
        restored, omitted = ms.getKeyValuePairs(oldSettingsDict,
                                                self.avrVersionOld.toString(),
                                                self.avrVersionNew.toString())

        printStdErr("Migrating these settings: " + json.dumps(restored.items()))
        printStdErr("Omitting these settings: " + json.dumps(omitted.items()))

        self.send_restored_settings(restored)


    def get_combined_settings_dict(self, oldSettings):
        combined = oldSettings.get('controlConstants').copy() # copy keys/values from controlConstants
        combined.update(oldSettings.get('controlSettings')) # add keys/values from controlSettings
        return combined

    def send_restored_settings(self, restoredSettings):
        for key in restoredSettings:
            command = "j{" + str(key) + ":" + str(restoredSettings[key]) + "}\n"
            self.ser.write(command)
            # make readline blocking for max 5 seconds to give the controller time to respond after every setting
            oldTimeout = self.ser.timeout
            self.ser.setTimeout(5)
            # read all replies
            while 1:
                line = self.ser.readline()
                if line:  # line available?
                    if line[0] == 'D':
                        self.print_debug_log(line)
                if self.ser.inWaiting() == 0:
                    break
            self.ser.setTimeout(oldTimeout)

    def restore_devices(self):
        ser = self.ser

        oldDevices = self.oldSettings.get('installedDevices')
        if oldDevices:
            printStdErr("Now trying to restore previously installed devices: " + str(oldDevices))
        else:
            printStdErr("No devices to restore!")
            return

        detectedDevices = None
        for device in oldDevices:
            printStdErr("Restoring device: " + json.dumps(device))
            if "a" in device.keys(): # check for sensors configured as first on bus
                if int(device['a'], 16) == 0:
                    printStdErr("OneWire sensor was configured to autodetect the first sensor on the bus, " +
                                "but this is no longer supported. " +
                                "We'll attempt to automatically find the address and add the sensor based on its address")
                    if detectedDevices is None:
                        ser.write("h{}")  # installed devices
                        time.sleep(1)
                        # get list of detected devices
                        for line in ser:
                            if line[0] == 'h':
                                detectedDevices = json_decode_response(line)

                    for detectedDevice in detectedDevices:
                        if device['p'] == detectedDevice['p']:
                            device['a'] = detectedDevice['a'] # get address from sensor that was first on bus

            ser.write("U" + json.dumps(device))

            time.sleep(3)  # give the Arduino time to respond

            # read log messages from arduino
            while 1:  # read all lines on serial interface
                line = ser.readline()
                if line:  # line available?
                    if line[0] == 'D':
                        self.print_debug_log(line)
                    elif line[0] == 'U':
                        printStdErr(("%(a)s reports: device updated to: " % msg_map) + line[2:])
                else:
                    break
        printStdErr("Restoring installed devices done!")


class SparkProgrammer(SerialProgrammer):
    def __init__(self, config, boardType):
        SerialProgrammer.__init__(self, config)

    def flash_file(self, hexFile):
        self.ser.write('F')
        line = self.ser.readline()
        printStdErr(line)
        time.sleep(0.2)

        file = open(hexFile, 'rb')
        result = LightYModem().transfer(file, self.ser, stderr)
        file.close()
        success = result==LightYModem.eot
        printStdErr("File flashed successfully" if success else "Problem flashing file: "+str(result))
        return success


class ArduinoProgrammer(SerialProgrammer):
    def __init__(self, config, boardType):
        SerialProgrammer.__init__(self, config)
        self.boardType = boardType

    def delay_serial_open(self):
        time.sleep(5)  # give the arduino some time to reboot in case of an Arduino UNO

    def reset_leonardo(self):
        del self.ser
        self.ser = None
        if self.open_serial(self.config, 1200, None):
            self.ser.close()
            time.sleep(2)  # give the bootloader time to start up
            self.ser = None
            return True
        else:
            printStdErr("Could not open serial port at 1200 baud to reset Arduino Leonardo")
            return False


    def flash_file(self, hexFile):
        config, boardType = self.config, self.boardType
        printStdErr("Loading programming settings from board.txt")
        arduinohome = config.get('arduinoHome', '/usr/share/arduino/')  # location of Arduino sdk
        avrdudehome = config.get('avrdudeHome', arduinohome + 'hardware/tools/')  # location of avr tools
        avrsizehome = config.get('avrsizeHome', '')  # default to empty string because avrsize is on path
        avrconf = config.get('avrConf', avrdudehome + 'avrdude.conf')  # location of global avr conf

        boardsFile = loadBoardsFile(arduinohome)
        boardSettings = fetchBoardSettings(boardsFile, boardType)

        # parse the Arduino board file to get the right program settings
        for line in boardsFile:
            if line.startswith(boardType):
                # strip board name, period and \n
                setting = line.replace(boardType + '.', '', 1).strip()
                [key, sign, val] = setting.rpartition('=')
                boardSettings[key] = val

        printStdErr("Checking hex file size with avr-size...")

        # start programming the Arduino
        avrsizeCommand = avrsizehome + 'avr-size ' + "\"" + hexFile + "\""

        # check program size against maximum size
        p = sub.Popen(avrsizeCommand, stdout=sub.PIPE, stderr=sub.PIPE, shell=True)
        output, errors = p.communicate()
        if errors != "":
            printStdErr('avr-size error: ' + errors)
            return False

        programSize = output.split()[7]
        printStdErr(('Program size: ' + programSize +
                     ' bytes out of max ' + boardSettings['upload.maximum_size']))

        # Another check just to be sure!
        if int(programSize) > int(boardSettings['upload.maximum_size']):
            printStdErr("ERROR: program size is bigger than maximum size for your Arduino " + boardType)
            return False

        hexFileDir = os.path.dirname(hexFile)
        hexFileLocal = os.path.basename(hexFile)

        if boardType == 'leonardo':
            if not self.reset_leonardo():
                return False

        programCommand = (avrdudehome + 'avrdude' +
                          ' -F ' +  # override device signature check
                          ' -e ' +  # erase flash and eeprom before programming. This prevents issues with corrupted EEPROM
                          ' -p ' + boardSettings['build.mcu'] +
                          ' -c ' + boardSettings['upload.protocol'] +
                          ' -b ' + boardSettings['upload.speed'] +
                          ' -P ' + self.port +
                          ' -U ' + 'flash:w:' + "\"" + hexFileLocal + "\"" +
                          ' -C ' + avrconf)

        printStdErr("Programming Arduino with avrdude: " + programCommand)


        p = sub.Popen(programCommand, stdout=sub.PIPE, stderr=sub.PIPE, shell=True, cwd=hexFileDir)
        output, errors = p.communicate()

        # avrdude only uses stderr, append its output to the returnString
        printStdErr("Result of invoking avrdude:\n" + errors)

        if("bytes of flash verified" in errors):
            printStdErr("Avrdude done, programming succesful!")
        else:
            printStdErr("There was an error while programming.")
            return False

        printStdErr("Giving the Arduino a few seconds to power up...")
        self.delay(6)
        return True

def test_program_spark_core():
    file = "R:\\dev\\brewpi\\firmware\\platform\\spark\\target\\brewpi.bin"
    config = { "port" : "COM22" }
    result = programController(config, "spark-core", file, { "settings":True, "devices":True})
    printStdErr("Result is "+str(result))

if __name__ == '__main__':
    test_program_spark_core()

