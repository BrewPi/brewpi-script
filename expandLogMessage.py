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

import brewpiJson
import simplejson as json
import parseEnum

logMessagesFile = '../brewpi-avr/brewpi_avr/logMessages.h'

errorDict = parseEnum.parseEnumInFile(logMessagesFile, 'errorMessages')
infoDict = parseEnum.parseEnumInFile(logMessagesFile, 'infoMessages')
warningDict = parseEnum.parseEnumInFile(logMessagesFile, 'warningMessages')

def valToFunction(val):
	if val == 0:
		return 'None'
	elif val == 1:
		return 'Chamber Door'
	elif val == 2:
		return 'Chamber Heater'
	elif val == 3:
		return 'Chamber Cooler'
	elif val == 4:
		return 'Chamber Light'
	elif val == 5:
		return 'Chamber Temp'
	elif val == 6:
		return 'Room Temp'
	elif val == 7:
		return 'Chamber Fan'
	elif val == 8:
		return 'Chamber Reserved 1'
	elif val == 9:
		return 'Beer Temp'
	elif val == 10:
		return  'Beer Temperature 2'
	elif val == 11:
		return  'Beer Heater'
	elif val == 12:
		return  'Beer Cooler'
	elif val == 13:
		return  'Beer S.G.'
	elif val == 14:
		return  'Beer Reserved 1'
	elif val == 15:
		return  'Beer Reserved 2'
	else:
		return 'Unknown Device Function'


def expandLogMessage(logMessageJsonString):
	expanded = ""
	logMessageJson = json.loads(logMessageJsonString)
	logId = int(logMessageJson['logID'])
	logType = logMessageJson['logType']
	values = logMessageJson['V']
	dict  = 0
	logTypeString = "**UNKNOWN MESSAGE TYPE**"
	if logType == "E":
		dict = errorDict
		logTypeString = "ERROR"
	elif logType == "W":
		dict = warningDict
		logTypeString = "WARNING"
	elif logType == "I":
		dict = infoDict
		logTypeString = "INFO MESSAGE"

	if logId in dict:
		expanded += logTypeString + " "
		expanded += str(logId) + ": "
		count = 0
		for v in values:
			try:
				if dict[logId]['paramNames'][count] == "config.deviceFunction":
					values[count] = valToFunction(v)
				elif dict[logId]['paramNames'][count] == "character":
					if values[count] == -1:
						# No character received
						values[count] = 'END OF INPUT'
					else:
						values[count] = chr(values[count])
			except IndexError:
				pass
			count += 1
		printString = dict[logId]['logString'].replace("%d", "%s").replace("%c", "%s")
		numVars = printString.count("%s")
		numReceived = len(values)
		if numVars == numReceived:
			expanded +=  printString % tuple(values)
		else:
			expanded += printString + "  | Number of arguments mismatch!, expected " + str(numVars) + "arguments, received " + str(values)
	else:
		expanded += logTypeString + " with unknown ID " + str(logId)

	return expanded
