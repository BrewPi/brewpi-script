__author__ = 'Elco'

from configobj import ConfigObj
import time
import sys


def addSlash(path):
	if not path.endswith('/'):
		path += '/'
	return path


def readCfgWithDefaults(cfg, defaultCfg):
	defaultConfig = ConfigObj('defaultCfg')
	if cfg:
		config = defaultConfig
		userConfig = ConfigObj(cfg)
		config.merge(userConfig)
	return config


def logMessage(message):
	print >> sys.stderr, time.strftime("%b %d %Y %H:%M:%S   ") + message
