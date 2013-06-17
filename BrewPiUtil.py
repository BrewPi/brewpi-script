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

from configobj import ConfigObj
import time
import sys


def addSlash(path):
	"""
	Adds a slash to the path, but only when it does not already have a slash at the end
	Params: a string
	Returns: a string
	"""
	if not path.endswith('/'):
		path += '/'
	return path


def readCfgWithDefaults(cfg, defaultCfg):
	"""
	Reads a config file with the default config file as fallback

	Params:
	cfg: string, path to cfg file
	defaultCfg: string, path to defaultConfig file.

	Returns:
	ConfigObj of settings
	"""
	defaultConfig = ConfigObj(defaultCfg)
	config = defaultConfig
	if cfg:
		userConfig = ConfigObj(cfg)
		config.merge(userConfig)
	return config


def logMessage(message):
	"""
	Prints a timestamped message to stderr
	"""
	print >> sys.stderr, time.strftime("%b %d %Y %H:%M:%S   ") + message
