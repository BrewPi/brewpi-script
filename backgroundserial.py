from __future__ import print_function

import threading
import Queue
import sys
import time
from BrewPiUtil import printStdErr
from BrewPiUtil import logMessage
from serial import SerialException

class BackGroundSerial():
    def __init__(self, serial_port):
        self.buffer = ''
        self.ser = serial_port
        self.queue = Queue.Queue()
        self.thread = None
        self.error = False
        self.fatal_error = None
        self.run = False

    # public interface only has 4 functions: start/stop/read_line/write
    def start(self):
        # write timeout will occur when there are problems with the serial port.
        # without the timeout loosing the serial port goes undetected.
        self.ser.write_timeout = 2
        self.run = True
        if not self.thread:
            self.thread = threading.Thread(target=self.__listenThread)
            self.thread.setDaemon(True)
            self.thread.start()

    def stop(self):
        self.run = False
        if self.thread:
            self.thread.join() # wait for background thread to terminate
            self.thread = None

    def read_line(self):
        self.exit_on_fatal_error()
        try:
            return self.queue.get_nowait()
        except Queue.Empty:
            return None

    def write(self, data):
        self.exit_on_fatal_error()
        # prevent writing to a port in error state. This will leave unclosed handles to serial on the system
        if not self.error:
            try:
                self.ser.write(data)
            except (IOError, OSError, SerialException) as e:
                logMessage('Serial Error: {0})'.format(str(e)))
                self.error = True


    def exit_on_fatal_error(self):
        if self.fatal_error is not None:
            self.stop()
            logMessage(self.fatal_error)
            if self.ser is not None:
                self.ser.close()
            del self.ser # this helps to fully release the port to the OS
            sys.exit("Terminating due to fatal serial error")

    def __listenThread(self):
        lastReceive = time.time()
        while self.run :
            in_waiting = None
            new_data = None
            if not self.error:
                try:
                    in_waiting = self.ser.inWaiting()
                    if in_waiting > 0:
                        new_data = self.ser.read(in_waiting)
                        lastReceive = time.time()
                except (IOError, OSError, SerialException) as e:
                    logMessage('Serial Error: {0})'.format(str(e)))
                    self.error = True

            if new_data:
                self.buffer = self.buffer + new_data
                line = self.__get_line_from_buffer()
                if line:
                    self.queue.put(line)

            if self.error:
                try:
                    # try to restore serial by closing and opening again
                    self.ser.close()
                    self.ser.open()
                    self.error = False
                except (ValueError, OSError, SerialException) as e:
                    if self.ser.isOpen():
                        self.ser.flushInput() # will help to close open handles
                        self.ser.flushOutput() # will help to close open handles
                    self.ser.close()
                    self.fatal_error = 'Lost serial connection. Error: {0})'.format(str(e))
                    self.run = False

            # max 10 ms delay. At baud 57600, max 576 characters are received while waiting
            time.sleep(0.01)

    def __get_line_from_buffer(self):
        while '\n' in self.buffer:
            lines = self.buffer.partition('\n') # returns 3-tuple with line, separator, rest
            if(lines[1] == ''):
                # '\n' not found, first element is incomplete line
                self.buffer = lines[0]
                return None
            else:
                # complete line received, [0] is complete line [1] is separator [2] is the rest
                self.buffer = lines[2]
                return self.__asciiToUnicode(lines[0])

    # remove extended ascii characters from string, because they can raise UnicodeDecodeError later
    def __asciiToUnicode(self, s):
        s = s.replace(chr(0xB0), '&deg')
        return unicode(s, 'ascii', 'ignore')

if __name__ == '__main__':
    # some test code that requests data from serial and processes the response json
    import simplejson
    import time
    import BrewPiUtil as util

    config_file = util.addSlash(sys.path[0]) + 'settings/config.cfg'
    config = util.readCfgWithDefaults(config_file)
    ser = util.setupSerial(config, time_out=0)
    if not ser:
        printStdErr("Could not open Serial Port")
        exit()

    bg_ser = BackGroundSerial(ser)
    bg_ser.start()

    success = 0
    fail = 0
    for i in range(1, 5):
        # request control variables 4 times. This would overrun buffer if it was not read in a background thread
        # the json decode will then fail, because the message is clipped
        bg_ser.write('v')
        bg_ser.write('v')
        bg_ser.write('v')
        bg_ser.write('v')
        bg_ser.write('v')
        line = True
        while(line):
            line = bg_ser.read_line()
            if line:
                if line[0] == 'V':
                    try:
                        decoded = simplejson.loads(line[2:])
                        print("Success")
                        success += 1
                    except simplejson.JSONDecodeError:
                        logMessage("Error: invalid JSON parameter string received: " + line)
                        fail += 1
                else:
                    print(line)
        time.sleep(5)

    print("Successes: {0}, Fails: {1}".format(success,fail))

