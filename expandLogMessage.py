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

def expandLogMessage(logMessageJsonString):
	ERROR_SRAM_SENSOR = 0
	ERROR_SENSOR_NO_ADDRESS_ON_PIN = 1
	ERROR_OUT_OF_MEMORY_FOR_DEVICE = 2
	ERROR_DEVICE_DEFINITION_UPDATE_SPEC_INVALID = 3
	ERROR_INVALID_CHAMBER = 4
	ERROR_INVALID_BEER = 5
	ERROR_INVALID_DEVICE_FUNCTION = 6
	INFO_SENSOR_CONNECTED = 100
	INFO_SENSOR_FETCHING_INITIAL_TEMP = 101
	INFO_UNINSTALL_TEMP_SENSOR = 102
	INFO_UNINSTALL_ACTUATOR = 103
	INFO_UNINSTALL_SWITCH_SENSOR = 104
	INFO_INSTALL_TEMP_SENSOR = 105
	INFO_INSTALL_ACTUATOR = 106
	INFO_INSTALL_SWITCH_SENSOR = 107
	INFO_INSTALL_DEVICE = 108
	INFO_DEVICE_DEFINITION = 109

	expanded = ""
	logMessageJson = json.loads(logMessageJsonString)
	logId = int(logMessageJson['logID'])
	logType = logMessageJson['logType']
	values = logMessageJson['V']

	if logType == "E":
		expanded += "ERROR "
	elif logType == "W":
		expanded += "WARNING "
	elif logType == "I":
		expanded += "INFO "

	expanded += str(logId) + ": "

	#  OneWireTempSensor.cpp
	if logId == ERROR_SRAM_SENSOR:
		expanded += "Not enough SRAM for temp sensor %s" % (values[0]['logString'])
	if logId == ERROR_SENSOR_NO_ADDRESS_ON_PIN:
		expanded += "Cannot find address for sensor on pin %s" % (values[0]['logString'])
	if logId == ERROR_OUT_OF_MEMORY_FOR_DEVICE:
		expanded += "*** OUT OF MEMORY for device f=%s" % (values[0]['logString'])
	#  DeviceManager.cpp
	if logId == ERROR_DEVICE_DEFINITION_UPDATE_SPEC_INVALID:
		expanded += "Device definition update specification is INVALID"
	if logId == ERROR_INVALID_CHAMBER:
		expanded += "INVALID chamber logId %s" % (values[0]['logString'])
	if logId == ERROR_INVALID_BEER:
		expanded += "INVALID beer logId %s" % (values[0]['logString'])
	if logId == ERROR_INVALID_DEVICE_FUNCTION:
		expanded += "INVALID device function logId %s" % (values[0]['logString'])
	#  Info messages
	#  OneWireTempSensor.cpp
	if logId == INFO_SENSOR_CONNECTED:
		expanded += "Temp sensor connected on pin %s" % (values[0]['logString'])
	if logId == INFO_SENSOR_FETCHING_INITIAL_TEMP:
		expanded += "Fetching initial temperature of sensor %s" % (values[0]['logString'])
	#  DeviceManager.cpp
	if logId == INFO_UNINSTALL_TEMP_SENSOR:
		expanded += "uninstalling temperature sensor  with function %s" % (values[0]['logString'])
	if logId == INFO_UNINSTALL_ACTUATOR:
		expanded += "uninstalling actuator with function %s" % (values[0]['logString'])
	if logId == INFO_UNINSTALL_SWITCH_SENSOR:
		expanded += "uninstalling switch sensor  with function %s" % (values[0]['logString'])
	if logId == INFO_INSTALL_TEMP_SENSOR:
		expanded += "installing temperature sensor  with function %s" % (values[0]['logString'])
	if logId == INFO_INSTALL_ACTUATOR:
		expanded += "installing actuator with function %s" % (values[0]['logString'])
	if logId == INFO_INSTALL_SWITCH_SENSOR:
		expanded += "installing switch sensor  with function %s" % (values[0]['logString'])
	if logId == INFO_INSTALL_DEVICE:
		expanded += "Installing device f=%s" % (values[0]['logString'])
	if logId == INFO_DEVICE_DEFINITION:
		expanded += "deviceDef %s:%s\n" % (values[0]['logString'], values[1]['logString'])

	return expanded
