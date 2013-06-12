__author__ = 'mat'


import simplejson as json

class AvrInfo:
	""" Parses and stores the version and other compile-time details reported by the Arduino """
	version = "v"
	build = "n"
	simulator = "y"
	board = "b"
	shield = "s"
	log = "l"

	shield_revA = "revA"
	shield_revC = "revC"

	shields = { 1:shield_revA, 2: shield_revC }

	board_leonardo = "leonardo"
	board_standard = "standard"
	board_mega = "mega"

	boards = {'l':board_leonardo, 's':board_standard, 'm':board_mega }

	def __init__(self, s = None):
		self.major = 0
		self.minor = 0
		self.revision = 0
		self.version = None
		self.build = 0
		self.simulator = False
		self.board = None
		self.shield = None
		self.log = 0
		self.parse(s)


	def parse(self, s):
		if s is None or len(s) == 0:
			pass
		else:
			s = s.strip()
			if s[0] == '{':
				self.parseJsonVersion(s)
			else:
				self.parseStringVersion(s)

	def parseJsonVersion(self, s):
		j = json.loads(s)
		if AvrInfo.version in j:
			self.parseStringVersion(j[AvrInfo.version])
		if AvrInfo.simulator in j:
			self.simulator = j[AvrInfo.simulator] == 1
		if AvrInfo.board in j:
			self.board = AvrInfo.boards.get(j[AvrInfo.board])
		if AvrInfo.shield in j:
			self.shield = AvrInfo.shields.get(j[AvrInfo.shield])
		if AvrInfo.log in j:
			self.log = j[AvrInfo.log]
		if AvrInfo.build in j:
			self.build = j[AvrInfo.build]

	def parseStringVersion(self, s):
		s = s.strip()
		parts = [int(x) for x in s.split('.')]
		parts += [0]*(3-len(parts))			# pad to 3
		self.major, self.minor, self.revision = parts[0],parts[1],parts[2]
		self.version = s





