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

def getVersionFromSerial(ser):
    version = None
    retries = 0
    requestVersion = True
    startTime = time.time()
    while requestVersion:
        retry = True
        for line in ser:
            if line[0] == 'N':
                data = line.strip('\n')[2:]
                version = AvrInfo(data)
                requestVersion = False
                retry = False
                break
            if time.time() - startTime > ser.timeout:
                # have read entire buffer, now just reading data as it comes in. Break to prevent an endless loop.
                break

        if retry:
            ser.write('n')  # request version info
            time.sleep(1)
            retries += 1
            if retries > 15:
                break
    return version


class AvrInfo:
    """ Parses and stores the version and other compile-time details reported by the Arduino """
    version = "v"
    build = "n"
    simulator = "y"
    board = "b"
    shield = "s"
    log = "l"
    commit = "c"

    shield_revA = "revA"
    shield_revC = "revC"

    shields = {1: shield_revA, 2: shield_revC}

    board_leonardo = "leonardo"
    board_standard = "standard"
    board_mega = "mega"

    boards = {'l': board_leonardo, 's': board_standard, 'm': board_mega}

    def __init__(self, s=None):
        self.major = 0
        self.minor = 0
        self.revision = 0
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
        try:
            j = json.loads(s)
        except json.decoder.JSONDecodeError, e:
            print >> sys.stderr, "JSON decode error: %s" % str(e)
            print >> sys.stderr, "Could not parse version number: " + s
        except UnicodeDecodeError, e:
            print >> sys.stderr, "Unicode decode error: %s" % str(e)
            print >> sys.stderr, "Could not parse version number: " + s

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
        if AvrInfo.commit in j:
            self.commit = j[AvrInfo.commit]

    def parseStringVersion(self, s):
        s = s.strip()
        parts = [int(x) for x in s.split('.')]
        parts += [0] * (3 - len(parts))			# pad to 3
        self.major, self.minor, self.revision = parts[0], parts[1], parts[2]
        self.version = s

    def toString(self):
        return str(self.major) + "." + str(self.minor) + "." + str(self.revision)

    def toExtendedString(self):
        string = "BrewPi v" + self.toString()
        if self.commit:
            string += ", running commit " + str(self.commit)
        if self.build:
            string += " build " + str(self.build)
        if self.board:
            string += ", on an Arduino " + str(self.board)
        if self.shield:
            string += " with a " + str(self.shield) + " shield"
        if(self.simulator):
           string += ", running as simulator"
        return string

