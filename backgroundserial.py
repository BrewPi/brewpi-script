from __future__ import print_function

import threading
import Queue
import sys
import time
from BrewPiUtil import printStdErr, logMessage
from serial import SerialException, serial_for_url
from expandLogMessage import filterOutLogMessages
import autoSerial

class BackGroundSerial():
    def __init__(self, port):
        self.buffer = ''
        self.port = port
        self.ser = None
        self.queue = Queue.Queue()
        self.messages = Queue.Queue()
        self.thread = None
        self.fatal_error = None
        self.stop_event = threading.Event()
        self.start()
        self.error = None

    # public interface only has 4 functions: start/stop/read_line/write
    def start(self):
        self.stop_event.clear()
        if not self.thread:
            self.thread = threading.Thread(target=self.__listen_thread, kwargs={'stop_event': self.stop_event})
            self.thread.setDaemon(True)
            self.thread.start()

    def stop(self):
        self.stop_event.set()
        if self.thread is not None:
            start = time.time()
            while(self.thread.isAlive()):
                time.sleep(0.1) # give time to close
                if time.time() - start > 5:
                    self.fatal_error = "Cannot stop Serial background thread"
                    break
            self.thread = None

    def connected(self):
        return self.ser is not None

    def read_line(self):
        self.exit_on_fatal_error()
        try:
            return self.queue.get_nowait()
        except Queue.Empty:
            return None

    def read_message(self):
        self.exit_on_fatal_error()
        try:
            return self.messages.get_nowait()
        except Queue.Empty:
            return None

    def writeln(self, data):
        return self.write(data + "\n")

    def write(self, data):
        self.exit_on_fatal_error()
        # Prevent writing to a port in error state.
        # This will leave unclosed handles to serial on the system
        written = 0
        if self.ser:
            try:
                written = self.ser.write(data)
            except (IOError, OSError, SerialException) as e:
                logMessage('Serial Error: {0})'.format(str(e)))
        return written

    def exit_on_fatal_error(self):
        if self.fatal_error is not None:
            self.stop()
            logMessage(self.fatal_error)
            sys.exit("Terminating due to fatal serial error")

    def __listen_thread(self, stop_event):
        logMessage('Background thread for serial started')
        while not stop_event.is_set():
            if not self.ser:
                if self.port == 'auto':
                    (serial_port, name) = autoSerial.detect_port(False)
                else:
                    serial_port = self.port
                try:
                    if serial_port is not None:
                        self.ser = serial_for_url(serial_port, baudrate=57600, timeout=0.1, write_timeout=0.1)
                        self.ser.inter_byte_timeout = 0.01 # necessary because of bug in in_waiting with sockets
                        self.ser.flushInput()
                        self.ser.flushOutput()
                        logMessage('Serial (re)connected at port: {0}'.format(str(serial_port)))
                except (IOError, OSError, SerialException) as e:
                    if self.ser:
                        self.ser.close()
                        self.ser = None
                    error = str(e)
                    if error != self.error:
                        #only print once
                        self.error = error
                        logMessage('Error opening serial: {0}'.format(self.error))
                    time.sleep(1)
            else:
                new_data = ""
                try:
                    while self.ser.in_waiting > 0:
                        # for sockets, in_waiting returns 1 instead of the actual number of bytes
                        # this is a workaround for that
                        new_data = new_data + self.ser.read(self.ser.in_waiting)
                except (IOError, OSError, SerialException) as e:
                    logMessage('Serial Error: {0})'.format(str(e)))
                    self.ser.close()
                    self.ser = None

                if len(new_data) > 0:
                    self.buffer = self.buffer + new_data
                    while True:
                        line_from_buffer = self.__get_line_from_buffer()
                        if line_from_buffer:
                            self.queue.put(line_from_buffer)
                        else:
                            break                   

            # max 10 ms delay. At baud 57600, max 576 characters are received while waiting
            time.sleep(0.01)

        logMessage('Background thread for serial stopped')
        if self.ser:
            self.ser.close()
            self.ser = None

    def __get_line_from_buffer(self):
        while '\n' in self.buffer:
            stripped_buffer, messages = filterOutLogMessages(self.buffer)
            if len(messages) > 0:
                for message in messages:
                    self.messages.put(message)
                self.buffer = stripped_buffer
                continue
            lines = self.buffer.partition('\n') # returns 3-tuple with line, separator, rest
            if not lines[1]:
                # '\n' not found, first element is incomplete line
                self.buffer = lines[0]
                return None
            else:
                # complete line received, [0] is complete line [1] is separator [2] is the rest
                self.buffer = lines[2]
                return self.__ascii_to_unicode(lines[0])

    # remove extended ascii characters from string, because they can raise UnicodeDecodeError later
    def __ascii_to_unicode(self, s):
        s = s.replace(chr(0xB0), '&deg')
        return unicode(s, 'ascii', 'ignore')

if __name__ == '__main__':
    # some test code that requests data from serial and processes the response json
    import simplejson
    import BrewPiUtil as util

    config_file = util.addSlash(sys.path[0]) + 'settings/config.cfg'
    config = util.readCfgWithDefaults(config_file)
    
    bg_ser = BackGroundSerial('auto')
    bg_ser.start()

    success = 0
    fail = 0
    for i in range(1, 5):
        # request control variables 4 times.
        # This would overrun buffer if it was not read in a background thread
        # the json decode will then fail, because the message is clipped
        bg_ser.writeln('v')
        bg_ser.writeln('v')
        bg_ser.writeln('v')
        bg_ser.writeln('v')
        bg_ser.writeln('v')
        line = True
        while line:
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

    print("Successes: {0}, Fails: {1}".format(success, fail))

