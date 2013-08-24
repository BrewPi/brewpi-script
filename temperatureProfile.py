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

import time
import csv


def getNewTemp(scriptPath):
	temperatureReader = csv.reader(
		open(scriptPath + 'settings/tempProfile.csv', 'rb'),
									delimiter=',', quoting=csv.QUOTE_ALL)
	temperatureReader.next()  # discard the first row, which is the table header
	prevTemp = -1
	nextTemp = -1
	prevDate = -1
	nextDate = -1
	interpolatedTemp = -1

	now = time.mktime(time.localtime())  # get current time in seconds since epoch

	for row in temperatureReader:
		datestring = row[0]
		if(datestring != "null"):
			temperature = float(row[1])
			prevTemp = nextTemp
			nextTemp = temperature
			prevDate = nextDate
			nextDate = time.mktime(time.strptime(datestring, "%Y/%m/%dT%H:%M:%S"))
			timeDiff = now - nextDate
			if(timeDiff < 0):
				if(prevDate == -1):
					interpolatedTemp = nextTemp  # first setpoint is in the future
					break
				else:
					interpolatedTemp = ((now - prevDate) / (nextDate - prevDate) *
										(nextTemp - prevTemp) + prevTemp)
					break

	if(interpolatedTemp == -1):  # all setpoints in the past
		interpolatedTemp = nextTemp
	return round(interpolatedTemp, 2)  # retun temp in tenths of degrees
