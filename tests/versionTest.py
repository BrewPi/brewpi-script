__author__ = 'mat'

import unittest
from brewpiVersion import AvrInfo


class VersionTestCase(unittest.TestCase):
	def assertVersionEqual(self, v, major, minor, rev, versionString):
		self.assertEqual(major, v.major)
		self.assertEqual(minor, v.minor)
		self.assertEqual(rev, v.revision)
		self.assertEqual(versionString, v.version)

	def assertEmptyVersion(self, v):
		self.assertVersionEqual(v, 0, 0, 0, None)

	def newVersion(self):
		return AvrInfo()

	def test_instantiatedVersionIsEmpty(self):
		v = self.newVersion()
		self.assertEmptyVersion(v)

	def test_parseSmptyStringIsEmptyVersion(self):
		v = self.newVersion()
		v.parse("")
		self.assertEmptyVersion(v)

	def test_parseNoStringIsEmptyVersion(self):
		v = self.newVersion()
		s = None
		v.parse(s)
		self.assertEmptyVersion(v)

	def test_canParseStringVersion(self):
		v = self.newVersion()
		v.parse("0.1.0")
		self.assertVersionEqual(v, 0, 1, 0, "0.1.0")

	def test_canParseJsonVersion(self):
		v = self.newVersion()
		v.parse('{"v":"0.1.0"}')
		self.assertVersionEqual(v, 0, 1, 0, "0.1.0")

	def test_canParseJsonSimulatorEnabled(self):
		v = self.newVersion()
		v.parse('{"y":1}')
		self.assertEqual(v.simulator, True)

	def test_canParseJsonSimulatorDisabled(self):
		v = self.newVersion()
		v.parse('{"y":0}')
		self.assertEqual(v.simulator, False)

	def test_canParseShieldRevC(self):
		v = self.newVersion()
		v.parse('{"s":2}')
		self.assertEqual(v.shield, AvrInfo.shield_revC)

	def test_canParseBoardLeonardo(self):
		v = self.newVersion()
		v.parse('{"b":"l"}')
		self.assertEqual(v.board, AvrInfo.board_leonardo)

	def test_canParseBoardStandard(self):
		v = self.newVersion()
		v.parse('{"b":"s"}')
		self.assertEqual(v.board, AvrInfo.board_standard)

	def test_canParseAll(self):
		v = AvrInfo('{"v":"1.2.3", "b":"l", "y":0, "s":2 }')
		self.assertVersionEqual(v, 1, 2, 3, "1.2.3")
		self.assertEqual(v.board, AvrInfo.board_leonardo)
		self.assertEqual(v.simulator, False)
		self.assertEqual(v.shield, AvrInfo.shield_revC)

if __name__ == '__main__':
	unittest.main()
