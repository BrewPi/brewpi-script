import os.path
# To change this template, choose Tools | Templates
# and open the template in the editor.

from programArduino import fetchBoardSettings
import os
import sys
import unittest
import programArduino
from configobj import ConfigObj


def loadDefaultConfig():
    currentScript = os.path.abspath( __file__ )
    currentDir = os.path.dirname(currentScript)
    configFile = os.path.abspath(currentDir + '/../settings/config.cfg')
    config = ConfigObj(configFile)
    return config

class  LoadBoardSettingsTestCase(unittest.TestCase):

    def setUp(self):
        self.config = loadDefaultConfig()
        self.boardsFile = programArduino.loadBoardsFile(self.config);
    #
    
    def test_loadBoardSettings_Leonardo(self):
        boardType = 'leonardo'
        self.assertBoardSettings(boardType, 28672);

    def test_loadBoardSettings_Mega2560(self):
        self.assertBoardSettings('mega2560', 258048)

    def assertBoardSettings(self, boardType, maxUploadSize):
        boardSettings = fetchBoardSettings(self.boardsFile, boardType);
        assert len(boardSettings) > 0
        self.assertEquals(int(boardSettings['upload.maximum_size']), maxUploadSize)


if __name__ == '__main__':
    unittest.main()

