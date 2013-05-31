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

from pprint import pprint
import serial
import time
import socket
import sys
import os
import shutil
import urllib
import re
import simplejson as json
from configobj import ConfigObj

#local imports
import temperatureProfile
import programArduino as programmer
import brewpiJson
from brewpiVersion import AvrInfo

# Settings will be read from Arduino, initialize with same defaults as Arduino
# This is mainly to show what's expected. Will all be overwritten on the first update from the arduino

compatibleBrewpiVersion = "0.1.1"

# Control Settings
cs = dict(mode='b', beerSetting=20.0, fridgeSetting=20.0, heatEstimator=0.2, coolEstimator=5)

# Control Constants
cc = dict(tempFormat="C", tempSetMin=1.0, tempSetMax=30.0, Kp=20.000, Ki=0.600, Kd=-3.000, iMaxErr=0.500,
          idleRangeH=1.000, idleRangeL=-1.000, heatTargetH=0.301, heatTargetL=-0.199, coolTargetH=0.199,
          coolTargetL=-0.301, maxHeatTimeForEst="600", maxCoolTimeForEst="1200", fridgeFastFilt="1", fridgeSlowFilt="4",
          fridgeSlopeFilt="3", beerFastFilt="3", beerSlowFilt="5", beerSlopeFilt="4", lah=0, hs=0)

# Control variables
cv = dict(beerDiff=0.000, diffIntegral=0.000, beerSlope=0.000, p=0.000, i=0.000, d=0.000, estPeak=0.000,
          negPeakEst=0.000, posPeakEst=0.000, negPeak=0.000, posPeak=0.000)

deviceList = {}

lcdText = ['Script starting up', ' ', ' ', ' ']

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


def configSet(settingName, value):
	global userConfig
	global config
	config[settingName] = value
	userConfig[settingName] = value
	userConfig.write()


localJsonFileName = ""
localCsvFileName = ""
wwwJsonFileName = ""
wwwCsvFileName = ""
lastDay = ""
day = ""

# wwwSettings.json is a copy of some of the settings for the web server
def changeWwwSetting(settingName, value):
	wwwSettingsFile = open(config['wwwPath'] + 'wwwSettings.json', 'r+b')
	wwwSettings = json.load(wwwSettingsFile)
	wwwSettings[settingName] = value
	wwwSettingsFile.seek(0)
	wwwSettingsFile.write(json.dumps(wwwSettings))
	wwwSettingsFile.truncate()
	wwwSettingsFile.close()


def startBeer(beerName):
	global config
	global localJsonFileName
	global localCsvFileName
	global wwwJsonFileName
	global wwwCsvFileName
	global lastDay
	global day

	# create directory for the data if it does not exist
	dataPath = addSlash(config['scriptPath']) + 'data/' + beerName + '/'
	wwwDataPath = addSlash(config['wwwPath']) + 'data/' + beerName + '/'

	if not os.path.exists(dataPath):
		os.makedirs(dataPath)
		os.chmod(dataPath, 0775)  # give group all permissions
	if not os.path.exists(wwwDataPath):
		os.makedirs(wwwDataPath)
		os.chmod(wwwDataPath, 0775)  # sudgive group all permissions

	# Keep track of day and make new data tabe for each day
	# This limits data table size, which can grow very big otherwise
	day = time.strftime("%Y-%m-%d")
	lastDay = day
	# define a JSON file to store the data table
	jsonFileName = config['beerName'] + '-' + day
	#if a file for today already existed, add suffix
	if os.path.isfile(dataPath + jsonFileName + '.json'):
		i = 1
		while os.path.isfile(dataPath + jsonFileName + '-' + str(i) + '.json'):
			i += 1
		jsonFileName = jsonFileName + '-' + str(i)
	localJsonFileName = dataPath + jsonFileName + '.json'
	brewpiJson.newEmptyFile(localJsonFileName)

	# Define a location on the web server to copy the file to after it is written
	wwwJsonFileName = wwwDataPath + jsonFileName + '.json'

	# Define a CSV file to store the data as CSV (might be useful one day)
	localCsvFileName = (dataPath + config['beerName'] + '.csv')
	wwwCsvFileName = (wwwDataPath + config['beerName'] + '.csv')
	changeWwwSetting('beerName', beerName)


def logMessage(message):
	print >> sys.stderr, time.strftime("%b %d %Y %H:%M:%S   ") + message

def fixJson(j):
	j = re.sub(r"{\s*?(\w)", r'{"\1', j)
	j = re.sub(r",\s*?(\w)", r',"\1', j)
	j = re.sub(r"(\w)?\s*:", r'\1":', j)
	j = re.sub(r":\s*(\w*)\s*([,}])", r':"\1"\2', j)
	return j


ser = 0
con = 0
# open serial port
try:
	port = config['port']
	ser = serial.Serial(port, 57600, timeout=1)
except serial.SerialException, e:
	print e
	exit()

dumpSerial = config.get('dumpSerial', False)

# yes this is monkey patching, but I don't see how to replace the methods on a dynamically instantiated type any other way
if dumpSerial:
	ser.readOriginal = ser.read
	ser.writeOriginal = ser.write
	def readAndDump(size=1):
		r = ser.readOriginal(size)
		sys.stdout.write(r)
		return r
	def writeAndDump(data):
		ser.writeOriginal(data)
		sys.stderr.write(data)
	ser.read = readAndDump
	ser.write = writeAndDump


logMessage("Notification: Script started for beer '" + config['beerName'] + "'")
# wait for 10 seconds to allow an Uno to reboot (in case an Uno is being used)
time.sleep(float(config.get('startupDelay', 10)))

ser.flush()
retries = 0
while 1:  # read all lines on serial interface
	line = ser.readline()
	if(line):  # line available?
		if(line[0] == 'N'):
			data = line.strip('\n')[2:]
			v = AvrInfo(data)
			brewpiVersion = v.version
			if(brewpiVersion == compatibleBrewpiVersion):
				print "Found BrewPi version " + brewpiVersion
			else:
				logMessage("Warning: BrewPi version compatible with this script is " +
						   compatibleBrewpiVersion +
						   " but version number received is " + brewpiVersion)
			break
	else:
		ser.write('n')
		time.sleep(1)
		retries += 1
		if retries > 5:
			logMessage("Warning: Cannot receive version number from Arduino. " +
				   "Script might not be compatible.")
			break

ser.flush()
# request settings from Arduino, processed later when reply is received
ser.write('s')  # request control settings cs
ser.write('c') # request control constants cc
# answer from Arduino is received asynchronously later.

def addSlash(path):
	if not path.endswith('/'):
		path += '/'
	return path

#create a listening socket to communicate with PHP
is_windows = sys.platform.startswith('win')
useInetSocket = bool(config.get('useInetSocket', is_windows));
if (useInetSocket):
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	port = config.get('socketPort', 6332)
	s.bind((config.get('socketHost', 'localhost'), int(port)))
	logMessage('Bound to TCP socket on port %d ' % port)
else:
	socketFile = addSlash(config['scriptPath']) + 'BEERSOCKET'
	if os.path.exists(socketFile):
	# if socket already exists, remove it
		os.remove(socketFile)
	s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
	s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	s.bind(socketFile)  # Bind BEERSOCKET
	# set all permissions for socket
	os.chmod(socketFile, 0777)
s.setblocking(1)  # set socket functions to be blocking
s.listen(10)  # Create a backlog queue for up to 5 connections
# blocking socket functions wait 'serialCheckInterval' seconds
s.settimeout(float(config['serialCheckInterval']))

prevDataTime = 0.0  # keep track of time between new data requests
prevTimeOut = time.time()

run = 1

startBeer(config['beerName'])
outputTemperature = True

prevTempJson = {
"BeerTemp":0,
"FridgeTemp":0,
"BeerAnn":None,
"FridgeAnn":None,
"RoomTemp":None,
"State":None,
"BeerSet":0,
"FridgeSet":0
}
def renameTempKey(key):
	rename = {
	"bt" : "BeerTemp",
	"bs" : "BeerSet",
	"ba":"BeerAnn",
	"ft":"FridgeTemp",
	"fs":"FridgeSet",
	"fa":"FridgeAnn",
	"rt":"RoomTemp",
	"s":"State",
	"t":"Time"
	}
	return rename.get(key, key)

while run:

	# Check whether it is a new day
	lastDay = day
	day = time.strftime("%Y-%m-%d")
	if lastDay != day:
		logMessage("Notification: New day, dropping data table and creating new JSON file.")
		jsonFileName = config['beerName'] + '/' + config['beerName'] + '-' + day
		localJsonFileName = addSlash(config['scriptPath']) + 'data/' + jsonFileName + '.json'
		wwwJsonFileName = addSlash(config['wwwPath']) + 'data/' + jsonFileName + '.json'
		# create new empty json file
		brewpiJson.newEmptyFile(localJsonFileName)

	# Wait for incoming socket connections.
	# When nothing is received, socket.timeout will be raised after
	# serialCheckInterval seconds. Serial receive will be done then.
	# When messages are expected on serial, the timeout is raised 'manually'
	try:
		conn, addr = s.accept()
		# blocking receive, times out in serialCheckInterval
		message = conn.recv(1024)
		if "=" in message:
			messageType, value = message.split("=", 1)
		else:
			messageType = message
			value = ""
		if messageType == "ack":  # acknowledge request
			conn.send('ack')
		elif messageType == "lcd":  # lcd contents requested
			conn.send(json.dumps(lcdText))
		elif messageType == "getMode":  # echo cs['mode'] setting
			conn.send(cs['mode'])
		elif messageType == "getFridge":  # echo fridge temperature setting
			conn.send(str(cs['fridgeSet']))
		elif messageType == "getBeer":  # echo fridge temperature setting
			conn.send(str(cs['beerSet']))
		elif messageType == "getControlConstants":
			conn.send(json.dumps(cc))
		elif messageType == "getControlSettings":
			conn.send(json.dumps(cs))
		elif messageType == "getControlVariables":
			conn.send(json.dumps(cv))
		elif messageType == "refreshControlConstants":
			ser.write("c")
			raise socket.timeout
		elif messageType == "refreshControlSettings":
			ser.write("s")
			raise socket.timeout
		elif messageType == "refreshControlVariables":
			ser.write("v")
			raise socket.timeout
		elif messageType == "loadDefaultControlSettings":
			ser.write("S")
			raise socket.timeout
		elif messageType == "loadDefaultControlConstants":
			ser.write("C")
			raise socket.timeout
		elif messageType == "setBeer":  # new constant beer temperature received
			newTemp = float(value)
			if cc['tempSetMin'] < newTemp < cc['tempSetMax']:
				cs['mode'] = 'b'
				# round to 2 dec, python will otherwise produce 6.999999999
				cs['beerSet'] = round(newTemp, 2)
				ser.write("j{mode:b, beerSet:" + str(cs['beerSet']) + "}")
				logMessage("Notification: Beer temperature set to " +
						   str(cs['beerSet']) +
						   " degrees in web interface")
				raise socket.timeout  # go to serial communication to update Arduino
			else:
				logMessage("Beer temperature setting" + str(newTemp) +
						   " is outside allowed range " +
						   str(cc['tempSetMin']) + "-" + str(cc['tempSetMax']))
		elif messageType == "setFridge":  # new constant fridge temperature received
			newTemp = float(value)
			if cc['tempSetMin'] < newTemp < cc['tempSetMax']:
				cs['mode'] = 'f'
				cs['fridgeSet'] = round(newTemp, 2)
				ser.write("j{mode:f, fridgeSet:" + str(cs['fridgeSet']) + "+")
				logMessage("Notification: Fridge temperature set to " +
						   str(cs['fridgeSet']) +
						   " degrees in web interface")
				raise socket.timeout  # go to serial communication to update Arduino
		elif messageType == "setProfile":  # cs['mode'] set to profile
			# read temperatures from currentprofile.csv
			cs['mode'] = 'p'
			cs['beerSet'] = temperatureProfile.getNewTemp(config['scriptPath'])
			ser.write("j{mode:p, beerSet:" + str(cs['beerSet']) + "}")
			logMessage("Notification: Profile mode enabled")
			raise socket.timeout  # go to serial communication to update Arduino
		elif messageType == "setOff":  # cs['mode'] set to OFF
			cs['mode'] = 'o'
			ser.write("j{mode:o}")
			logMessage("Notification: Temperature control disabled")
			raise socket.timeout
		elif messageType == "setParameters":
			# receive JSON key:value pairs to set parameters on the Arduino
			try:
				decoded = json.loads(value)
				ser.write("j" + json.dumps(decoded))
				if 'tempFormat' in decoded:
					changeWwwSetting('tempFormat', decoded['tempFormat'])  # change in web interface settings too.
			except json.JSONDecodeError:
				logMessage("Error: invalid JSON parameter string received: " + value)
			raise socket.timeout
		elif messageType == "stopScript":  # exit instruction received. Stop script.
			run = 0
			# voluntary shutdown.
			# write a file to prevent the cron job from restarting the script
			dontrunfile = open(config['wwwPath'] + 'do_not_run_brewpi', "w")
			dontrunfile.write("1")
			dontrunfile.close()
			continue
		elif messageType == "interval":  # new interval received
			newInterval = int(value)
			if 5 < newInterval < 5000:
				configSet('interval',float(newInterval))
				logMessage("Notification: Interval changed to " +
						   str(newInterval) + " seconds")
		elif messageType == "name":  # new beer name
			newName = value
			if len(newName) > 3:     # shorter names are probably invalid
				configSet('beerName', newName)
				startBeer(newName)
				logMessage("Notification: restarted for beer: " + newName)
		elif messageType == "profileKey":
			configSet('profileKey', value)
			changeWwwSetting('profileKey', value)
		elif messageType == "uploadProfile":
			# use urllib to download the profile as a CSV file
			profileUrl = ("https://spreadsheets.google.com/tq?key=" +
						  config['profileKey'] +
						  "&tq=select D,E&tqx=out:csv")  # select the right cells and CSV format
			profileFileName = config['scriptPath'] + 'settings/tempProfile.csv'
			if os.path.isfile(profileFileName + '.old'):
				os.remove(profileFileName + '.old')
			os.rename(profileFileName, profileFileName + '.old')
			urllib.urlretrieve(profileUrl, profileFileName)
			if os.path.isfile(profileFileName):
				conn.send("Profile successfuly updated")
			else:
				conn.send("Failed to update profile")
		elif messageType == "programArduino":
			ser.close  # close serial port before programming
			del ser  # Arduino won't reset when serial port is not completely removed
			try:
				programParameters = json.loads(value)
			except json.JSONDecodeError:
				logMessage("Error: cannot decode programming parameters: " + value)
			hexFile = programParameters['fileName']
			boardType = programParameters['boardType']
			port = config['port']
			eraseEEPROM = programParameters['eraseEEPROM']
			logMessage("New program uploaded to Arduino, script will restart")
			result = programmer.programArduino(config, boardType, hexFile, port, eraseEEPROM)

			# avrdudeResult = programmer.programArduino(	programParameters['boardType'],
			#							programParameters['fileName'],
			#							config['port'],
			#							programParameters['eraseEEPROM'])
			conn.send(result)
			# restart the script when done. This replaces this process with the new one
			time.sleep(5)  # give the Arduino time to reboot
			python = sys.executable
			os.execl(python, python, *sys.argv)
		elif messageType == "refreshDeviceList":
			ser.write("h{" + value + "}")  # value contains request parameters in JSON
		elif messageType == "getDeviceList":
			conn.send(json.dumps(deviceList))
		elif messageType == "applyDevice":
			try:
				configStringJson = json.loads(fixJson(value))  # load as JSON to check syntax
			except json.JSONDecodeError:
				logMessage("Error: invalid JSON parameter string received: " + value)
				continue

			ser.write("U" + value)
		else:
			logMessage("Error: Received invalid message on socket: " + message)

		if (time.time() - prevTimeOut) < config['serialCheckInterval']:
			continue
		else:
			# raise exception to check serial for data immediately
			raise socket.timeout

	except socket.timeout:
		# Do serial communication and update settings every SerialCheckInterval
		prevTimeOut = time.time()

		# request new LCD text
		ser.write('l')
		# request Settings from Arduino to stay up to date
		ser.write('s')

		# if no new data has been received for serialRequestInteval seconds
		if (time.time() - prevDataTime) >= float(config['interval']):
			ser.write("t")  # request new from arduino

		elif ((time.time() - prevDataTime) > float(config['interval']) +
			  2 * float(config['interval'])):
			#something is wrong: arduino is not responding to data requests
			logMessage("Error: Arduino is not responding to new data requests")

		while 1:  # read all lines on serial interface
			line = ser.readline()
			if line:  # line available?
				try:
					if line[0] == 'T':

						# print it to stdout
						if outputTemperature:
							print time.strftime("%b %d %Y %H:%M:%S  ") + line[2:]
						# process temperature line
						newData = json.loads(line[2:])
						# copy/rename keys
						for key in newData:
							prevTempJson[renameTempKey(key)] = newData[key]

						newRow = prevTempJson
						# add to JSON file
						brewpiJson.addRow(localJsonFileName, newRow)
						# copy to www dir.
						# Do not write directly to www dir to prevent blocking www file.
						shutil.copyfile(localJsonFileName, wwwJsonFileName)
						#write csv file too
						csvFile = open(localCsvFileName, "a")
						try:
							lineToWrite = (time.strftime("%b %d %Y %H:%M:%S;") +
										   str(newRow['BeerTemp']) + ';' +
										   str(newRow['BeerSet']) + ';' +
										   str(newRow['BeerAnn']) + ';' +
										   str(newRow['FridgeTemp']) + ';' +
										   str(newRow['FridgeSet']) + ';' +
										   str(newRow['FridgeAnn']) + ';' +
										   str(newRow['State']) + ';' +
										   str(newRow['RoomTemp']) + '\n')
							csvFile.write(lineToWrite)
						except KeyError, e:
							logMessage("KeyError in line from Arduino: %s" % e)

						csvFile.close()
						shutil.copyfile(localCsvFileName, wwwCsvFileName)
						# store time of last new data for interval check
						prevDataTime = time.time()
					elif line[0] == 'D':
						# debug message received
						logMessage("Arduino debug message: " + line[2:])
					elif line[0] == 'L':
						# lcd content received
						lcdTextReplaced = line[2:].replace('\xb0', '&deg')  # replace degree sign with &deg
						lcdText = json.loads(lcdTextReplaced)
					elif line[0] == 'C':
						# Control constants received
						cc = json.loads(line[2:])
						# pprint(cc, sys.stderr)
					elif line[0] == 'S':
						# Control settings received
						cs = json.loads(line[2:])
					# do not print this to the log file. This is requested continuously.
					elif line[0] == 'V':
						# Control settings received
						cv = json.loads(line[2:])
						# pprint(cv, sys.stderr)
					elif line[0] == 'N':
						pass  # version number received. Do nothing, just ignore
					elif line[0] == 'h':
						fixedJson = fixJson(line[2:])
						print fixedJson
						deviceList = json.loads(fixedJson)
						pprint(deviceList)
					else:
						logMessage("Cannot process line from Arduino: " + line)
					# end or processing a line
				except json.decoder.JSONDecodeError, e:
					logMessage("JSON decode error: %s" % e)
					logMessage("Line received was: " + line)
			else:
				# no lines left to process
				break

		# Check for update from temperature profile
		if cs['mode'] == 'p':
			newTemp = temperatureProfile.getNewTemp(config['scriptPath'])
			if cc['tempSetMin'] < newTemp < cc['tempSetMax']:
				if newTemp != cs['beerSet']:
					# if temperature has to be updated send settings to arduino
					cs['beerSet'] = temperatureProfile.getNewTemp(config['scriptPath'])
					ser.write("j{beerSet:" + str(cs['beerSet']) + "}")

	except socket.error, e:
		logMessage("socket error: %s" % e)

if ser:
	ser.close()  # close port
if conn:
	conn.shutdown(socket.SHUT_RDWR)  # close socket
	conn.close()
