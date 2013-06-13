import os.path
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

import subprocess as sub
import serial
import time
import simplejson as json
import os
from brewpiVersion import AvrInfo
import expandLogMessage
import settingRestore
from sys import stderr

def printAndAdd(oldString, string):
	print >> stderr, string + '\n'
	return oldString + string

def printList(returnString, list):
	for item in list:
		printAndAdd(returnString, item)  # print one item per line

def fetchBoardSettings(boardsFile, boardType):
	boardSettings = {}
	for line in boardsFile:
		if(line.startswith(boardType)):
			setting = line.replace(boardType + '.', '', 1).strip() # strip board name, period and \n
			[key, sign, val] = setting.rpartition('=')
			boardSettings[key] = val
	return boardSettings

def loadBoardsFile(arduinohome):
	return open(arduinohome+'hardware/arduino/boards.txt', 'rb').readlines()

def programArduino(config, boardType, hexFile, restoreWhat):
	arduinohome = config.get('arduinoHome', '/usr/share/arduino/')  # location of Arduino sdk
	avrdudehome = config.get('avrdudeHome', arduinohome + 'hardware/tools/')  # location of avr tools
	avrsizehome = config.get('avrsizeHome', '')  # default to empty string because avrsize is on path
	avrconf = config.get('avrConf', avrdudehome + 'avrdude.conf')  # location of global avr conf
	returnString = ""

	boardsFile = loadBoardsFile(arduinohome)
	boardSettings = fetchBoardSettings(boardsFile, boardType)
	port = config['port']

	restoreSettings = False
	restoreDevices = False
	if 'settings' in restoreWhat:
		if restoreWhat['settings'] == True:
			restoreSettings = True
	if 'devices' in restoreWhat:
		if restoreWhat['devices'] == True:
			restoreDevices = True
	# Even when restoreSettings and restoreDevices are set to True here,
	# they might be set to false due to version incompatibility later


	# open serial port to read old settings and version
	try:
		ser = serial.Serial(port, 57600, timeout=1)  # timeout=1 is too slow when waiting on temp sensor reads
	except serial.SerialException, e:
		print e

	retries = 0
	while 1:  # read all lines on serial interface
		line = ser.readline()
		if line:  # line available?
			if line[0] == 'N':
				data = line.strip('\n')[2:]
				avrVersionOld = AvrInfo(data)
				printAndAdd(returnString,  "Checking old version before programming.")
				printAndAdd(returnString, ( "Found Arduino " + str(avrVersionOld.board) +
							" with a " + str(avrVersionOld.shield) + " shield, " +
							"running BrewPi version " + str(avrVersionOld.version) +
							" build " + str(avrVersionOld.build)))
				break
		else:
			ser.write('n')  # request version info
			time.sleep(1)
			retries += 1
			if retries > 5:
				printAndAdd(returnString,  ("Warning: Cannot receive version number from Arduino. " +
							 "Your Arduino is either not programmed yet or running a very old version of BrewPi. "
							 "Arduino will be reset to defaults."))
				break

	ser.flush()

	oldSettings = {}

	# request all settings from board before programming
	ser.write("d{}")  # installed devices
	ser.write("c{}")  # control constants
	ser.write("s{}")  # control settings
	time.sleep(1)

	printAndAdd(returnString,  "Requesting old settings from Arduino...")

	while 1:  # read all lines on serial interface
		line = ser.readline()
		if line:  # line available?
			try:
				if line[0] == 'C':
					oldSettings['controlConstants'] = json.loads(line[2:])
				elif line[0] == 'S':
					oldSettings['controlSettings'] = json.loads(line[2:])
				elif line[0] == 'd':
					oldSettings['installedDevices'] = json.loads(line[2:])

			except json.decoder.JSONDecodeError, e:
				printAndAdd(returnString,  "JSON decode error: " + e)
				printAndAdd(returnString,  "Line received was: " + line)
		else:
			break

	ser.close()
	del ser  # Arduino won't reset when serial port is not completely removed
	oldSettingsFileName = 'oldAvrSettings-' + time.strftime("%b-%d-%Y-%H-%M-%S") + '.json'
	printAndAdd(returnString,  "Saving old settings to file "+ oldSettingsFileName)

	scriptDir = "" # os.path.dirname(__file__)  # <-- absolute dir the script is in
	oldSettingsFile = open(scriptDir + 'settings/' + oldSettingsFileName, 'wb')
	oldSettingsFile.write(json.dumps(oldSettings))

	oldSettingsFile.truncate()
	oldSettingsFile.close()


	# parse the Arduino board file to get the right program settings
	for line in boardsFile:
		if line.startswith(boardType):
			# strip board name, period and \n
			setting = line.replace(boardType + '.', '', 1).strip()
			[key, sign, val] = setting.rpartition('=')
			boardSettings[key] = val

	# start programming the Arduino
	avrsizeCommand = avrsizehome + 'avr-size ' + hexFile
	printAndAdd(returnString, avrsizeCommand)
	# check program size against maximum size
	p = sub.Popen(avrsizeCommand, stdout=sub.PIPE, stderr=sub.PIPE, shell=True)
	output, errors = p.communicate()
	if errors != "":
		printAndAdd(returnString, 'avr-size error: ' + errors)
		return returnString

	programSize = output.split()[7]
	printAndAdd(returnString, ('Progam size: ' + programSize +
		' bytes out of max ' + boardSettings['upload.maximum_size']))

	# Another check just to be sure!
	if int(programSize) > int(boardSettings['upload.maximum_size']):
		printAndAdd(returnString,  "ERROR: program size is bigger than maximum size for Arduino " + boardType)
		return returnString

	hexFileDir = os.path.dirname(hexFile)
	hexFileLocal = os.path.basename(hexFile)

	programCommand = (avrdudehome + 'avrdude' +
				' -F ' +
				' -p ' + boardSettings['build.mcu'] +
				' -c ' + boardSettings['upload.protocol'] +
				' -b ' + boardSettings['upload.speed'] +
				' -P ' + port +
				' -U ' + 'flash:w:' + hexFileLocal +
				' -C ' + avrconf)

	printAndAdd(returnString, programCommand)

	# open and close serial port at 1200 baud. This resets the Arduino Leonardo
	# the Arduino Uno resets every time the serial port is opened automatically
	if(boardType == 'leonardo'):
		ser = serial.Serial(port, 1200)
		ser.close()
		time.sleep(1)  # give the bootloader time to start up

	p = sub.Popen(programCommand, stdout=sub.PIPE, stderr=sub.PIPE, shell=True,cwd=hexFileDir)
	output, errors = p.communicate()

	# avrdude only uses stderr, append its output to the returnString
	printAndAdd(returnString, errors)

	printAndAdd(returnString,  "avrdude done! Now trying to restore settings")

	try:
		ser = serial.Serial(port, 57600, timeout=1)  # timeout=1 is too slow when waiting on temp sensor reads
	except serial.SerialException, e:
		print e
		printAndAdd(returnString,  "Error opening serial port after programming: " + e)

	retries = 0
	# read new version
	while 1:  # read all lines on serial interface
		line = ser.readline()
		if line:  # line available?
			if line[0] == 'N':
				data = line.strip('\n')[2:]
				avrVersionNew = AvrInfo(data)
				printAndAdd(returnString, ( "Checking new version: Found Arduino " + avrVersionNew.board +
				                 " with a " + str(avrVersionNew.shield) + " shield, " +
				                 "running BrewPi version " + str(avrVersionNew.version) +
				                 " build " + str(avrVersionNew.build) + "\n"))
				break
		else:
			ser.write('n')  # request version info
			time.sleep(1)
			retries += 1
			if retries > 10:
				printAndAdd(returnString,("Warning: Cannot receive version number from Arduino after programming. " +
				                 "Something must have gone wrong. \n"))
				break

	printAndAdd(returnString, "Checking if settings can be restored")

	if avrVersionNew.major == 0 and avrVersionNew.minor == 2:
		if avrVersionOld.major == 0:
			if avrVersionOld.minor == 0:
				printAndAdd(returnString,  "Could not receive version number from old board, " +\
			                "resetting to defaults without restoring settings.")
				restoreDevices = False
				restoreSettings = False
			if avrVersionOld.major > 0:
				# version 0.1.x, try to restore most of the settings
				settingsRestoreLookupDict = settingRestore.keys_0_1_x_to_0_2_0
				printAndAdd(returnString,  "Settings can be partially restored when going from 0.1.x to 0.2.0")
				restoreDevices = False

			if avrVersionOld.minor == 2:
				# restore settings and devices
				settingsRestoreLookupDict = settingRestore.keys_0_2_0_to_0_2_0
				printAndAdd(returnString,  "Settings can be fully restored when going from 0.2.0 to 0.2.0")
	else:
		printAndAdd(returnString, "Sorry, settings can only be restored when updating to BrewPi 0.2.0 or higher")

	printAndAdd(returnString, "Resetting EEPROM to default settings")
	lines = ser.readlines()
	for line in lines:
		if line[0] == 'D':
			# debug message received
			try:
				expandedMessage = expandLogMessage.expandLogMessage(line[2:])
			except Exception, e:  # catch all exceptions, because out of date file could cause errors
				printAndAdd(returnString, "Error while expanding log message: " + e)
			printAndAdd(returnString,  "Arduino debug message: " + expandedMessage)

	if restoreSettings:
		restoredSettings = {}
		ccOld = oldSettings['controlConstants']
		csOld = oldSettings['controlSettings']

		ser.write('c{}');
		ser.write('s{}');

		while 1:  # read all lines on serial interface
			line = ser.readline()
			if line:  # line available?
				try:
					if line[0] == 'C':
						ccNew = json.loads(line[2:])
					elif line[0] == 'S':
						csNew = json.loads(line[2:])
					elif line[0] == 'D':
						try: # debug message received
							expandedMessage = expandLogMessage.expandLogMessage(line[2:])
						except Exception, e:  # catch all exceptions, because out of date file could cause errors
							printAndAdd(returnString, "Error while expanding log message: " + e)
							printAndAdd(returnString, "Arduino debug message: " + expandedMessage)
				except json.decoder.JSONDecodeError, e:
						printAndAdd(returnString,  "JSON decode error: " + e)
						printAndAdd(returnString,  "Line received was: " + line)
			else:
				break

		printAndAdd(returnString, "Trying to restore old control constants and settings")
		# find control constants to restore
		for key in ccNew.keys():  # for all new keys
			for alias in settingRestore.getAliases(settingsRestoreLookupDict, key):  # get the valid aliases of old keys
				if alias in ccOld.keys():  # if they are in the old settings
					restoredSettings[key] = ccOld[alias]  # add the old setting to the restoredSettings

		# find control settings to restore
		for key in csNew.keys():  # for all new keys
			for alias in settingRestore.getAliases(settingsRestoreLookupDict, key):  # get the valid aliases of old keys
				if alias in csOld.keys():  # if they are in the old settings
					restoredSettings[key] = csOld[alias]  # add the old setting to the restoredSettings

		printAndAdd(returnString, "Restoring these settings: " + json.dumps(restoredSettings))
		ser.write("j" + json.dumps(restoredSettings))

		# read log messages from arduino
		while 1:  # read all lines on serial interface
			line = ser.readline()
			if line:  # line available?
				if line[0] == 'D':
					try: # debug message received
						expandedMessage = expandLogMessage.expandLogMessage(line[2:])
					except Exception, e:  # catch all exceptions, because out of date file could cause errors
						printAndAdd(returnString, "Error while expanding log message: " + e)
						printAndAdd(returnString, "Arduino debug message: " + expandedMessage)
			else:
				break

		printAndAdd(returnString, "restoring settings done!")

	if restoreDevices:
		printAndAdd(returnString, "Now trying to restore previously installed devices: " + str(oldSettings['installedDevices']))
		for device in oldSettings['installedDevices']:
			printAndAdd(returnString, "Restoring device: " + json.dumps(device))
			ser.write("U" + json.dumps(device))

		time.sleep(1) # give the Arduino time to respond

		# read log messages from arduino
		while 1:  # read all lines on serial interface
			line = ser.readline()
			if line:  # line available?
				if line[0] == 'D':
					try: # debug message received
						expandedMessage = expandLogMessage.expandLogMessage(line[2:])
					except Exception, e:  # catch all exceptions, because out of date file could cause errors
						printAndAdd(returnString, "Error while expanding log message: " + e)
						printAndAdd(returnString, "Arduino debug message: " + expandedMessage)
				elif line[0] == 'U':
					printAndAdd(returnString, "Arduino reports: device updated to: " + line[2:])
			else:
				break

		printAndAdd(returnString, "Restoring installed devices done!")

	ser.close()
	return returnString
