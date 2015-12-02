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

import distutils.spawn
import time
import os
import platform
import getopt
import subprocess
import re
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/..") # append parent directory to be able to import files
from gitHubReleases import gitHubReleases
import BrewPiUtil as util
import autoSerial
import serial
from programController import SerialProgrammer

releases = gitHubReleases("https://api.github.com/repos/brewpi/firmware")

serialPorts = []

# Read in command line arguments
try:
    opts, args = getopt.getopt(sys.argv[1:], "hf:t:ma",
                               ['help', 'file=', 'multi', 'tag=', 'testmode', 'autodfu', 'testmode'])
except getopt.GetoptError:
    print "Unknown parameter, available Options: --file, --multi, --tag --autodfu --testmode"

    sys.exit()

multi = False
testMode = False
autoDfu = False
tag = None
# binaries for system update
system1 = None
system2 = None
# binary to flash
binFile = None


for o, a in opts:
    # print help message for command line options
    if o in ('-h', '--help'):
        print "\n Available command line options: "
        print "--help: print this help message"
        print "--file: path to .bin file to flash instead of the latest release on GitHub"
        print "--tag: specify which tag to download from github"
        print "--multi: keep the script alive to flash multiple devices"
        print "--autodfu: automatically reboot photon in DFU mode by opening serial port at 14400 baud"
        print "--testmode: set controller o test mode after flashing"

        exit()
    # supply a config file
    if o in ('-f', '--file'):
        print("Using local files instead of downloading a release. \n")
        if os.path.isdir(a):
            for file in os.listdir(a):
                if all(x in file for x in ['brewpi', '.bin']):
                    binFile = os.path.join(os.path.abspath(a), file)
                if all(x in file for x in ['system', 'part1', '.bin']):
                    system1 = os.path.join(os.path.abspath(a), file)
                if all(x in file for x in ['system', 'part2', '.bin']):
                    system2 = os.path.join(os.path.abspath(a), file)
        else:
            binFile = os.path.abspath(a)
        if not os.path.exists(binFile):
            print('ERROR: Binary file(s) "%s" was not found!' % binFile)
            exit(1)
        if os.path.exists(system1) and os.path.exists(system2):
            print('System update files found, will update system part before flashing user binary. \n')
    # send quit instruction to all running instances of BrewPi
    if o in ('-m', '--multi'):
        multi = True
        print "Started in multi flash mode"
    if o in ('-t', '--tag'):
        tag = a
        print "Will try to download release '{0}'".format(tag)
    if o in ('--testmode'):
        testMode = True
        print "Will set device to test mode after flashing"
    if o in ('-a', '--autodfu'):
        autoDfu = True
        print "Will automatically reboot newly detected photons into DFU mode"

dfuPath = "dfu-util"
# check whether dfu-util can be found
if distutils.spawn.find_executable('dfu-util') is None:
    if platform.system() == "Windows":
        p = subprocess.Popen("where dfu-util", stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        p.wait()
        output, errors = p.communicate()
        if not output:
            print "dfu-util cannot be found, please add its location to your PATH variable"
            exit(1)
    elif platform.system() == "Linux":
        # TODO: change this block to be platform / architecture agnositc
        # as it currently expects you to be running from a Pi
        downloadDir = os.path.join(os.path.dirname(__file__), "downloads/")
        dfuPath = os.path.join(downloadDir, "dfu-util")
        if not os.path.exists(dfuPath):
            print "dfu-util not found, downloading dfu-util..."
            dfuUrl = "http://dfu-util.sourceforge.net/releases/dfu-util-0.7-binaries/linux-armel/dfu-util"
            if not os.path.exists(downloadDir):
                os.makedirs(downloadDir, 0777)
            releases.download(dfuUrl, downloadDir)
            os.chmod(dfuPath, 0777) # make executable
    else:
        print "This script is written for Linux or Windows only. We'll gladly take pull requests for other platforms."
        exit(1)

firstLoop = True
print "Detecting DFU devices"
while(True):
    # list DFU devices to see whether a device is connected
    p = subprocess.Popen(dfuPath + " -l", stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    p.wait()
    output, errors = p.communicate()
    if errors:
        print errors

    DFUs = re.findall(r'\[([0-9a-f]{4}:[0-9a-f]{4})\].*alt=0', output) # find hex format [0123:abcd]
    if len(DFUs) > 0:
        print "Found {0} devices: ".format(len(DFUs)), DFUs

    if len(DFUs) > 1:
        print "Please only connect one device at a time and try again."
        exit(1)
    elif len(DFUs) == 1:

        if DFUs[0] == '1d50:607f':
            type = 'core'
            print "Device identified as Spark Core"
        elif DFUs[0] == '2b04:d006':
            type = 'photon'
            print "Device identified as Particle Photon"
        else:
            print "Could not identify device as Photon or Spark Core. Exiting"
            exit(1)

        # download latest binary from GitHub if file not specified
        if not binFile:
            print "Downloading latest firmware..."
            if tag is None:
                tag = releases.getLatestTag()
                print "Latest stable version on GitHub: " + tag

            binFile = releases.getBin(tag, [type, 'brewpi', '.bin'])
            if binFile:
                print "Firmware downloaded to " + binFile
            else:
                print "Could not find download in release {0} with these words in the file name: {1}".format(tag, type)
                exit(1)

            if type == 'photon':
                system1 = releases.getBin(tag, ['photon', 'system-part1', '.bin'])
                system2 = releases.getBin(tag, ['photon', 'system-part2', '.bin'])

                if system1:
                    print "Release contains updated system firmware for the photon"
                    if not system2:
                        print "Error: system firmware part2 not found in release"
                        exit()

        if binFile:
            if type == 'core':
                print "Now writing BrewPi firmware {0}".format(binFile)
                p = subprocess.Popen(dfuPath + " -d 1d50:607f -a 0 -s 0x08005000:leave -D {0}".format(binFile), shell=True)
                p.wait()
            elif type == 'photon':
                if system1:
                    print "First updating system firmware for the Photon"
                    p = subprocess.Popen(dfuPath + " -d 2b04:d006 -a 0 -s 0x8020000 -D {0}".format(system1), shell=True)
                    p.wait()
                    p = subprocess.Popen(dfuPath + " -d 2b04:d006 -a 0 -s 0x8060000 -D {0}".format(system2), shell=True)
                    p.wait()

                print "Now writing BrewPi firmware {0}".format(binFile)
                p = subprocess.Popen(dfuPath + " -d 0x2B04:0xD006 -a 0 -s 0x80A0000:leave -D {0}".format(binFile), shell=True)
                p.wait()

            print "Programming done, now resetting EEPROM to defaults"
            # reset EEPROM to defaults
            configFile = util.scriptPath() + '/settings/config.cfg'
            config = util.readCfgWithDefaults(configFile)
            programmer = SerialProgrammer.create(config, "core")

            # open serial port
            print "Opening serial port"
            retries = 10
            while retries > 0:
                if programmer.open_serial(config, 57600, 0.2):
                    break
                retries -= 1
                time.sleep(1)
            if retries > 0:
                programmer.fetch_version("Success! ")
                programmer.reset_settings(testMode)
                serialPorts = autoSerial.detect_all_ports() # update serial ports here so device will not be seen as new
            else:
                print "Could not open serial port after programming"
        else:
            print "found DFU device, but no binary specified for flashing"
        if not multi:
            break
    else:
        if firstLoop:
            print "Did not find any DFU devices."
            print "Is your Photon or Spark Core running in DFU mode (blinking yellow)?"
            print "Waiting until a DFU device is connected..."
            serialPorts = autoSerial.detect_all_ports()
        firstLoop = False
        if autoDfu:
            previousSerialPorts = serialPorts
            serialPorts = autoSerial.detect_all_ports()
            newPorts = list(set(serialPorts) - set(previousSerialPorts))
            if len(newPorts):
                print "Found new serial port connected: {0}".format(newPorts[0])
                port = newPorts[0][0]
                name = newPorts[0][1]
                if name == "Particle Photon":
                    print "Putting Photon in DFU mode"
                    ser = serial.Serial(port)
                    try:
                        ser.setBaudrate(14400) # this triggers a reboot in DFU mode
                    except ValueError:
                        pass # because device reboots while reconfiguring an exception is thrown, ignore
                    ser.close()

    time.sleep(1)
