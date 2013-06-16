__author__ = 'Elco'

import psutil
import pprint
from configobj import ConfigObj
import BrewPiSocket
import BrewPiUtil as util


class BrewPiProcess:
	"""
	This class represents a running BrewPi process.
	It allows other instances of BrewPi to see if there would be conflicts between them.
	It can also use the socket to send a quit signal or the pid to kill the other instance.
	"""
	def __init__(self):
		self.cwd = None  # working directory of process
		self.pid = None  # pid of process
		self.cfg = None  # config file of process, full path
		self.port = None  # serial port the process is connected to
		self.sock = None  # socket the process is connected to

	def as_dict(self):
		return self.__dict__

	def quit(self):
		self.sock.start()


class BrewPiProcesses():
	"""
	This class can get all running BrewPi instances on the system as a list of BrewPiProcess objects.
	"""
	def __init__(self):
		self.list = []

	def update(self):
		bpList = []
		matching = [p for p in psutil.process_iter() if any('brewpi.py'in s for s in p.cmdline)]
		for p in matching:
			bp = BrewPiProcess()
			bp.cwd = p.getcwd()
			bp.pid = p._pid

			cfg = [s for s in p.cmdline if '.cfg' in s]  # get config file argument
			if cfg:
				cfg = bp.cwd + '/' + cfg[0]  # add full path to config file
			defaultCfg = bp.cwd + '/settings/config.cfg'
			bp.cfg = util.readCfgWithDefaults(cfg, defaultCfg)

			bp.port = bp.cfg['port']
			bp.sock = BrewPiSocket.BrewPiSocket(bp.cfg)

			bpList.append(bp)
		self.list = bpList
		return self.list

	def get(self):
		return self.list

	def as_dict(self):
		outputList = []
		for bp in self.list:
			outputList.append(bp.as_dict())
		return outputList

allScripts = BrewPiProcesses()
allScripts.update()
pprint.pprint(allScripts.as_dict())






