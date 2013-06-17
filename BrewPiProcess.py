__author__ = 'Elco'

import psutil
import pprint
import BrewPiSocket
import BrewPiUtil as util
import os
from time import sleep


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
		self.sock = None  # BrewPiSocket object which the process is connected to

	def as_dict(self):
		"""
		Returns: member variables as a dictionary
		"""
		return self.__dict__

	def quit(self):
		"""
		Sends a friendly quit message to this BrewPi process over its socket to aks the process to exit.
		"""
		if self.sock is not None:
			sock = self.sock.connect()
			sock.send('quit')
			sock.close()  # do not shutdown the socket, other processes are still connected to it.

	def kill(self):
		"""
		Kills this BrewPiProcess with force, use when quit fails.
		"""
		process = psutil.Process(self.pid)  # get psutil process my pid
		process.kill()


class BrewPiProcesses():
	"""
	This class can get all running BrewPi instances on the system as a list of BrewPiProcess objects.
	"""
	def __init__(self):
		self.list = []

	def update(self):
		"""
		Update the list of BrewPi processes by receiving them from the system with psutil.
		Returns: list of BrewPiProcess objects
		"""
		bpList = []
		matching = [p for p in psutil.process_iter() if any('brewpi.py'in s for s in p.cmdline)]
		for p in matching:
			bp = self.parseProcess(p)
			bpList.append(bp)
		self.list = bpList
		return self.list

	def parseProcess(self, process):
		"""
		Converts a psutil process into a BrewPiProcess object by parsing the config file it has been called with.
		Params: a psutil.Process object
		Returns: BrewPiProcess object
		"""
		bp = BrewPiProcess()
		bp.cwd = process.getcwd()
		bp.pid = process._pid

		cfg = [s for s in process.cmdline if '.cfg' in s]  # get config file argument
		if cfg:
			cfg = bp.cwd + '/' + cfg[0]  # add full path to config file
		defaultCfg = bp.cwd + '/settings/config.cfg'
		bp.cfg = util.readCfgWithDefaults(cfg, defaultCfg)

		bp.port = bp.cfg['port']
		bp.sock = BrewPiSocket.BrewPiSocket(bp.cfg)
		return bp

	def get(self):
		"""
		Returns a non-updated list of BrewPiProcess objects
		"""
		return self.list

	def me(self):
		"""
		Get a BrewPiProcess object of the process this function is called from
		"""
		myPid = os.getpid()
		myProcess = psutil.Process(myPid)
		return self.parseProcess(myProcess)

	def as_dict(self):
		"""
		Returns the list of BrewPiProcesses as a list of dicts
		"""
		outputList = []
		for bp in self.list:
			outputList.append(bp.as_dict())
		return outputList

	def __repr__(self):
		"""
		Print BrewPiProcesses as a dict when passed to a print statement
		"""
		return repr(self.as_dict())

	def quitAll(self):
		"""
		Ask all running BrewPi processes to exit
		"""
		self.update()
		for script in self.list:
			script.quit()

	def killAll(self):
		"""
		Kill all running BrewPi processes with force by sending a sigkill signal.
		"""
		self.update()
		for script in self.list:
			script.kill()


def testKillAll():
	"""
	Test function that prints the process list, sends a kill signal to all processes and prints the updated list again.
	"""
	allScripts = BrewPiProcesses()
	allScripts.update()
	print ("Running instances of BrewPi before killing them:")
	pprint.pprint(allScripts)
	allScripts.killAll()
	allScripts.update()
	print ("Running instances of BrewPi before after them:")
	pprint.pprint(allScripts)


def testQuitAll():
	"""
	Test function that prints the process list, sends a quit signal to all processes and prints the updated list again.
	"""
	allScripts = BrewPiProcesses()
	allScripts.update()
	print ("Running instances of BrewPi before asking them to quit:")
	pprint.pprint(allScripts)
	allScripts.quitAll()
	sleep(2)
	allScripts.update()
	print ("Running instances of BrewPi after asking them to quit:")
	pprint.pprint(allScripts)
