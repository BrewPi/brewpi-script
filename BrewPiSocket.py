__author__ = 'Elco'

from configobj import ConfigObj
import sys
import BrewPiUtil as util

class BrewPiSocket:
	def __init__(self, cfg):
		self.type = 'f'  # default to file socket
		self.file = None
		self.host = 'localhost'
		self.port = None

		isWindows = sys.platform.startswith('win')
		useInternetSocket = bool(cfg.get('useInternetSocket', isWindows))
		if useInternetSocket:
			self.port = cfg.get('socketPort', 6332)
			self.type = 'i'
		else:
			self.file = util.addSlash(cfg['scriptPath']) + 'BEERSOCKET'

	def __repr__(self):
		return repr(self.__dict__)
