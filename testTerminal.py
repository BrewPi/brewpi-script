# Copyright 2012 BrewPi
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

import serial
import time
import msvcrt
import sys
import os
from configobj import ConfigObj
import simplejson as json
import expandLogMessage

# Read in command line arguments
if len(sys.argv) < 2:
	print >> sys.stderr, 'Using default config path ./settings/config.cfg, to override use : %s <config file full path>' % sys.argv[0]
	configFile = './settings/config.cfg'
else:
	configFile = sys.argv[1]

if not os.path.exists(configFile):
	sys.exit('ERROR: Config file "%s" was not found!' % configFile)

# global variables, will be initialized by startBeer()
defaultConfig = ConfigObj('./settings/defaults.cfg')
userConfig = ConfigObj(configFile)
config = defaultConfig
config.merge(userConfig)

print "***** BrewPi Windows Test Terminal ****"
print "This simple Python script lets you send commands to the Arduino."
print "It also echoes everything the Arduino returns."
print "On known debug ID's in JSON format, it expands the messages to the full message"
print "press 's' to send a string to the Arduino, press 'q' to quit"

ser = 0

# open serial port
try:
	ser = serial.Serial(config['port'], 57600, timeout=1)
except serial.SerialException, e:
	print e
	exit()

while 1:
	if msvcrt.kbhit():
		received = msvcrt.getch()
		if received == 's':
			print "type the string you want to send to the Arduino: "
			userInput = raw_input()
			print "sending: " + userInput
			ser.write(userInput)
		elif received == 'q':
			exit()

	line = ser.readline()
	if line:
		if(line[0]=='D'):
			try:
				decoded = json.loads(line[2:])
				print "debug message received: " + expandLogMessage.expandLogMessage(line[2:])
			except json.JSONDecodeError:
				# print line normally, is not json
				print "debug message received: " + line[2:]

		else:
			print line

