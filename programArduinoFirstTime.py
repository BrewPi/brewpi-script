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

import os
import sys
from configobj import ConfigObj

import programController as programmer
import BrewPiUtil as util

# Read in command line arguments
if len(sys.argv) < 2:
	sys.exit('Usage: %s <config file full path>' % sys.argv[0])
if not os.path.exists(sys.argv[1]):
	sys.exit('ERROR: Config file "%s" was not found!' % sys.argv[1])

configFile = sys.argv[1]
config = ConfigObj(configFile)

# global variables, will be initialized by startBeer()
util.readCfgWithDefaults(configFile)

hexFile = config['wwwPath'] + 'uploads/brewpi-uno-revC.hex'
boardType = config['boardType']

result = programmer.programController(config, boardType, hexFile, {'settings': True, 'devices': True})

print result
