# Copyright 2015 BrewPi
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

import sys
# Check needed software dependencies to nudge users to fix their setup
if sys.version_info < (2, 7):
    print "Sorry, requires Python 2.7."
    sys.exit(1)

import time
import os
import getopt
import subprocess
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/..") # append parent directory to be able to import files
from gitHubReleases import gitHubReleases
import BrewPiUtil as util
from programController import SerialProgrammer

releases = gitHubReleases("https://api.github.com/repos/BrewPi/firmware")

# Read in command line arguments
try:
    opts, args = getopt.getopt(sys.argv[1:], "hf:mt",
                               ['help', 'file=', 'multi', 'testmode'])
except getopt.GetoptError:
    print "Unknown parameter, available Options: --file, --multi, --testmode"

    sys.exit()

multi = False
binFile = None
testMode = False

for o, a in opts:
    # print help message for command line options
    if o in ('-h', '--help'):
        print "\n Available command line options: "
        print "--help: print this help message"
        print "--file: path to .bin file to flash instead of the latest release on GitHub"
        print "--multi: keep the script alive to flash multiple devices"
        print "--testmode: set controller o test mode after flashing"

        exit()
    # supply a config file
    if o in ('-f', '--config'):
        binFile = os.path.abspath(a)
        if not os.path.exists(binFile):
            sys.exit('ERROR: Binary file "%s" was not found!' % binFile)
    # send quit instruction to all running instances of BrewPi
    if o in ('-m', '--multi'):
        multi = True
        print "Started in multi flash mode"
    if o in ('-t', '--testmode'):
        testMode = True
        print "Will set device to test mode after flashing"

dfuPath = "dfu-util"
# check whether dfu-util can be found
if sys.platform.startswith('win'):
    p = subprocess.Popen("where dfu-util", stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    p.wait()
    output, errors = p.communicate()
    if not output:
        print "dfu-util cannot be found, please add its location to your PATH variable"
        exit(1)
else:
    downloadDir = os.path.join(os.path.dirname(__file__), "downloads/")
    dfuPath = os.path.join(downloadDir, "dfu-util")
    if not os.path.exists(dfuPath):
        print "dfu-util not found, downloading dfu-util..."
        dfuUrl = "http://dfu-util.sourceforge.net/releases/dfu-util-0.7-binaries/linux-armel/dfu-util"
        if not os.path.exists(downloadDir):
            os.makedirs(downloadDir, 0777)
        releases.download(dfuUrl, downloadDir)
        os.chmod(dfuPath, 0777) # make executable

# download latest binary from GitHub if file not specified
if not binFile:
    print "Downloading latest firmware..."
    latest = releases.getLatestTag()
    print "Latest version on GitHub: " + latest

    binFile = releases.getBin(latest, ["spark-core", ".bin"])
    if binFile:
        print "Latest firmware downloaded to " + binFile
    else:
        print "Downloading firmware failed"
        exit(-1)

firstLoop = True
while(True):
    # list DFU devices to see whether a device is connected
    p = subprocess.Popen(dfuPath + " -l", stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    p.wait()
    output, errors = p.communicate()
    if errors:
        print errors
    if "Found" in output:
        # found a DFU device, flash the binary file to it
        if binFile:
            print "found DFU device, now flashing %s \n\n" % binFile

            p = subprocess.Popen(dfuPath + " dfu-util -d 1d50:607f -a 0 -s 0x08005000:leave -D %s" % binFile, shell=True)
            p.wait()

            # reset EEPROM to defaults
            configFile = util.scriptPath() + '/settings/config.cfg'
            config = util.readCfgWithDefaults(configFile)
            programmer = SerialProgrammer.create(config, "spark-core")

            # open serial port
            retries = 30
            while retries > 0:
                time.sleep(1)
                if programmer.open_serial(config, 57600, 0.2):
                    break
                retries -= 1
            if retries > 0:
                programmer.fetch_version("Success! ")
                programmer.reset_settings(testMode)
                print "Programming done!"
            else:
                print "Could not open serial port after programming"
        else:
            print "found DFU device, but no binary specified for flashing"
        if not multi:
            break
    else:
        if firstLoop:
            print "Did not find any DFU devices."
            print "Is your Spark Core running in DFU mode (blinking yellow)?"
            print "Waiting until a DFU device is connected..."
        firstLoop = False

    time.sleep(1)
