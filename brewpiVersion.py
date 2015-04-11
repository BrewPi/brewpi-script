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

import simplejson as json
import sys
import time
from distutils.version import LooseVersion

def getVersionFromSerial(ser):
    version = None
    retries = 0
    startTime = time.time()
    oldTimeOut = ser.timeout
    ser.setTimeout(1)
    ser.write('n')  # request version info
    while True:
        retry = True
        line = ser.readline()
        if line:
            if line[0] == 'N':
                data = line.strip('\n')[2:]
                version = AvrInfo(data)
                retry = False
            if time.time() - startTime >= ser.timeout:
                # have read entire buffer, now just reading data as it comes in. Break to prevent an endless loop.
                retry = False

        if retry:
            ser.write('n')  # request version info
            # time.sleep(1) delay not needed because of blocking (timeout) readline
            retries += 1
            if retries > 10:
                break
        else:
            break
    ser.setTimeout(oldTimeOut) # restore previous serial timeout value
    return version


class AvrInfo:
    """ Parses and stores the version and other compile-time details reported by the controller """
    version = "v"
    build = "n"
    simulator = "y"
    board = "b"
    shield = "s"
    log = "l"
    commit = "c"

    shield_revA = "revA"
    shield_revC = "revC"
    spark_shield_revC = "Rev-C"

    shields = {1: shield_revA, 2: shield_revC, 3: spark_shield_revC}

    board_leonardo = "leonardo"
    board_standard = "standard"
    board_mega = "mega"
    board_spark_core = "spark-core"

    boards = {'l': board_leonardo, 's': board_standard, 'm': board_mega, 'x': board_spark_core}

    family_arduino = "Arduino"
    family_spark = "Spark"

    families = { board_leonardo: family_arduino,
                board_standard: family_arduino,
                board_mega: family_arduino,
                board_spark_core: family_spark}

    board_names = { board_leonardo: "Leonardo",
                board_standard: "Uno",
                board_mega: "Mega",
                board_spark_core: "Core"}

    def __init__(self, s=None):
        self.version = None
        self.build = 0
        self.commit = None
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
        j = None
        try:
            j = json.loads(s)
        except json.decoder.JSONDecodeError, e:
            print >> sys.stderr, "JSON decode error: %s" % str(e)
            print >> sys.stderr, "Could not parse version number: " + s
        except UnicodeDecodeError, e:
            print >> sys.stderr, "Unicode decode error: %s" % str(e)
            print >> sys.stderr, "Could not parse version number: " + s

        self.family = None
        self.board_name = None
        if AvrInfo.version in j:
            self.parseStringVersion(j[AvrInfo.version])
        if AvrInfo.simulator in j:
            self.simulator = j[AvrInfo.simulator] == 1
        if AvrInfo.board in j:
            self.board = AvrInfo.boards.get(j[AvrInfo.board])
            self.family = AvrInfo.families.get(self.board)
            self.board_name = AvrInfo.board_names.get(self.board)
        if AvrInfo.shield in j:
            self.shield = AvrInfo.shields.get(j[AvrInfo.shield])
        if AvrInfo.log in j:
            self.log = j[AvrInfo.log]
        if AvrInfo.build in j:
            self.build = j[AvrInfo.build]
        if AvrInfo.commit in j:
            self.commit = j[AvrInfo.commit]

    def parseStringVersion(self, s):
        self.version = LooseVersion(s)

    def toString(self):
        if self.version:
            return str(self.version)
        else:
            return "0.0.0"

    def article(self, word):
        return "a" if not word[1].lower() not in 'aeiou' else "an"

    def toExtendedString(self):
        string = "BrewPi v" + self.toString()
        if self.commit:
            string += ", running commit " + str(self.commit)
        if self.build:
            string += " build " + str(self.build)
        if self.board:
            string += ", running on "+ self.article(self.family) + " " + str(self.family) + " " + str(self.board_name)
        if self.shield:
            string += " with a " + str(self.shield) + " shield"
        if(self.simulator):
           string += ", running as simulator"
        return string
