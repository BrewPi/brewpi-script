#!/usr/bin/python
# Copyright 2015 BrewPi, Elco Jacobs
# This file is part of BrewPi.

# BrewPi is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# BrewPi is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with BrewPi. If not, see <http://www.gnu.org/licenses/>.


from __future__ import print_function
import sys
import os
import subprocess

sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/..") # append parent directory to be able to import files

# print everything in this file to stderr so it ends up in the correct log file for the web UI
def printStdErr(*objs):
    print("", *objs, file=sys.stderr)

# Quits all running instances of BrewPi
def quitBrewPi(webPath):
    import BrewPiProcess
    allProcesses = BrewPiProcess.BrewPiProcesses()
    allProcesses.stopAll(webPath + "/do_not_run_brewpi")


def updateFromGitHub(userInput = False, restoreSettings = True, restoreDevices = True):
    import BrewPiUtil as util
    from gitHubReleases import gitHubReleases
    import brewpiVersion
    import programController as programmer

    configFile = util.scriptPath() + '/settings/config.cfg'
    config = util.readCfgWithDefaults(configFile)

    printStdErr("Stopping any running instances of BrewPi to check/update controller...")
    quitBrewPi(config['wwwPath'])

    hwVersion = None
    shield = None
    board = None
    boardName = None
    family = None
    ser = None

    ### Get version number
    printStdErr("\nChecking current firmware version...")
    try:
        ser = util.setupSerial(config)
        hwVersion = brewpiVersion.getVersionFromSerial(ser)
        family = hwVersion.family
        shield = hwVersion.shield
        board = hwVersion.board
        boardName = hwVersion.boardName()

        printStdErr("Found " + hwVersion.toExtendedString() + \
               " on port " + ser.name + "\n")
    except:
        printStdErr("Unable to connect to controller, perhaps it is disconnected or otherwise unavailable.")
        return -1

    if ser:
        ser.close()  # close serial port
        ser = None

    if not hwVersion:
        printStdErr("Unable to retrieve firmware version from controller")
        printStdErr("If your controller has not been programmed with an earlier version of BrewPi,"
                    " follow these instructions:")
        printStdErr("\n If you have an Arduino:")
        printStdErr("Please go to https://github.com/BrewPi/firmware/releases to download"
                    "the firmware and upload via the BrewPi web interface")
        printStdErr("\n If you have a Spark Core:")
        printStdErr("Put it in DFU mode and run: sudo /home/brewpi/utils/flashDfu.py")
    else:
        printStdErr("Current firmware version on controller: " + hwVersion.toString())

    printStdErr("\nChecking GitHub for latest release...")
    releases = gitHubReleases("https://api.github.com/repos/BrewPi/firmware")
    tag = releases.getLatestTag()
    printStdErr("Latest version on GitHub: " + tag)


    if hwVersion.isNewer(tag):
        printStdErr("\nVersion on GitHub is newer than your current version, downloading new version...")
    else:
        printStdErr("\nYour current firmware version is up-to-date. There is no need to update.")
        if userInput:
            printStdErr("If you are encountering problems, you can reprogram anyway."
                        " Would you like to do this?"
                        "\nType yes to reprogram or just press enter to keep your current firmware: ")
            choice = raw_input()
            if not any(choice == x for x in ["yes", "Yes", "YES", "yes", "y", "Y"]):
                return 0
            printStdErr("Would you like me to try to restore you settings after programming? [Y/n]: ")
            choice = raw_input()
            if not any(choice == x for x in ["", "yes", "Yes", "YES", "yes", "y", "Y"]):
                restoreSettings = False
            printStdErr("Would you like me to try to restore your configured devices after programming? [Y/n]: ")
            choice = raw_input()
            if not any(choice == x for x in ["", "yes", "Yes", "YES", "yes", "y", "Y"]):
                restoreDevices = False
        else:
            return 0

    printStdErr("Downloading latest firmware...")
    localFileName = None
    system1 = None
    system2 = None

    if family == "Arduino":
        localFileName = releases.getBin(tag, [boardName, shield, ".hex"])
    elif family == "Spark" or family == "Particle":
        localFileName = releases.getBin(tag, [boardName, 'brewpi', '.bin'])
    else:
        printStdErr("Error: Device family {0} not recognized".format(family))
        return -1

    if boardName == "Photon":
        latestSystemTag = releases.getLatestTagForSystem()
        if hwVersion.isNewer(latestSystemTag):
            printStdErr("Updated system firmware for the photon found in release {0}".format(latestSystemTag))
            system1 = releases.getBin(latestSystemTag, ['photon', 'system-part1', '.bin'])
            system2 = releases.getBin(latestSystemTag, ['photon', 'system-part2', '.bin'])
            if system1:
                printStdErr("Downloaded new system firmware to:\n")
                printStdErr("{0} and\n".format(system1))
                if not system2:
                    printStdErr("{0}\n".format(system2))
                    printStdErr("Error: system firmware part2 not found in release")
                    return -1

    if localFileName:
        printStdErr("Latest firmware downloaded to " + localFileName)
    else:
        printStdErr("Downloading firmware failed")
        return -1

    printStdErr("\nUpdating firmware over Serial...\n")
    result = programmer.programController(config, board, localFileName, system1, system2,
                                          {'settings': restoreSettings, 'devices': restoreDevices})
    util.removeDontRunFile(config['wwwPath'] + "/do_not_run_brewpi")
    return result

if __name__ == '__main__':
    import getopt
    # Read in command line arguments
    try:
        opts, args = getopt.getopt(sys.argv[1:], "s", ['silent'])
    except getopt.GetoptError:
        print ("Unknown parameter, available options: \n" +
              "  updaterFirmware.py --silent\t\t not use default options, do not ask for user input")
        sys.exit()

    userInput = True
    for o, a in opts:
        # print help message for command line options
        if o in ('-s', '--silent'):
            userInput = False

    result = updateFromGitHub(userInput)
    exit(result)