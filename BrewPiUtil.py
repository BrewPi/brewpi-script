# Copyright 2013 BrewPi
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
import sys
import os

try:
	import configobj
except ImportError:
	print "BrewPi requires ConfigObj to run, please install it with 'sudo apt-get install python-configobj"
	sys.exit(1)


def addSlash(path):
	"""
	Adds a slash to the path, but only when it does not already have a slash at the end
	Params: a string
	Returns: a string
	"""
	if not path.endswith('/'):
		path += '/'
	return path


def readCfgWithDefaults(cfg):
	"""
	Reads a config file with the default config file as fallback

	Params:
	cfg: string, path to cfg file
	defaultCfg: string, path to defaultConfig file.

	Returns:
	ConfigObj of settings
	"""
	defaultCfg = scriptPath() + '/settings/defaults.cfg'
	config = configobj.ConfigObj(defaultCfg)

	if cfg:
		try:
			userConfig = configobj.ConfigObj(cfg)
			config.merge(userConfig)
		except configobj.ParseError:
			logMessage("ERROR: Could not parse user config file %s" % cfg)
		except IOError:
			logMessage("Could not open user config file %s. Using only default config file" % cfg)
	return config


def configSet(configFile, settingName, value):
	if not os.path.isfile(configFile):
		logMessage("User config file %s does not exist yet, creating it..." % configFile)
	try:
		config = configobj.ConfigObj(configFile)
		config[settingName] = value
		config.write()
	except IOError as e:
		logMessage("I/O error(%d) while updating %s: %s " % (e.errno, configFile, e.strerror))
		logMessage("Probably your permissions are not set correctly. " +
		           "To fix this, run 'sudo sh /home/brewpi/fixPermissions.sh'")
	return readCfgWithDefaults(configFile)  # return updated ConfigObj


def logMessage(message):
	"""
	Prints a timestamped message to stderr
	"""
	print >> sys.stderr, time.strftime("%b %d %Y %H:%M:%S   ") + message


def scriptPath():
	"""
	Return the path of BrewPiUtil.py. __file__ only works in modules, not in the main script.
	That is why this function is needed.
	"""
	return os.path.dirname(__file__)
