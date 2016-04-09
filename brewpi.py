#!/usr/bin/python
# Copyright 2012 BrewPi
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

from __future__ import print_function
import sys

from BrewPiUtil import printStdErr
from BrewPiUtil import logMessage

# Check needed software dependencies to nudge users to fix their setup
if sys.version_info < (2, 7):
    printStdErr("Sorry, requires Python 2.7.")
    sys.exit(1)

# standard libraries
import time
import socket
import os
import getopt
from pprint import pprint
import shutil
import traceback
import urllib
from distutils.version import LooseVersion
from serial import SerialException

# load non standard packages, exit when they are not installed
try:
    import serial
    if LooseVersion(serial.VERSION) < LooseVersion("3.0"):
        printStdErr("BrewPi requires pyserial 3.0, you have version {0} installed.\n".format(serial.VERSION) +
                             "Please upgrade pyserial via pip, by running:\n" +
                             "  sudo pip install pyserial --upgrade\n" +
                             "If you do not have pip installed, install it with:\n" +
                             "  sudo apt-get install build-essential python-dev python-pip\n")
        sys.exit(1)
except ImportError:
    printStdErr("BrewPi requires PySerial to run, please install it via pip, by running:\n" +
                             "  sudo pip install pyserial --upgrade\n" +
                             "If you do not have pip installed, install it with:\n" +
                             "  sudo apt-get install build-essential python-dev python-pip\n")
    sys.exit(1)
try:
    import simplejson as json
except ImportError:
    printStdErr("BrewPi requires simplejson to run, please install it with 'sudo apt-get install python-simplejson")
    sys.exit(1)
try:
    from configobj import ConfigObj
except ImportError:
    printStdErr("BrewPi requires ConfigObj to run, please install it with 'sudo apt-get install python-configobj")
    sys.exit(1)


#local imports
import temperatureProfile
import programController as programmer
import brewpiJson
import BrewPiUtil as util
import brewpiVersion
import pinList
import expandLogMessage
import BrewPiProcess
from backgroundserial import BackGroundSerial


# Settings will be read from controller, initialize with same defaults as controller
# This is mainly to show what's expected. Will all be overwritten on the first update from the controller

compatibleHwVersion = "0.2.4"

# Control Settings
cs = dict(mode='b', beerSet=20.0, fridgeSet=20.0, heatEstimator=0.2, coolEstimator=5)

# Control Constants
cc = dict(tempFormat="C", tempSetMin=1.0, tempSetMax=30.0, pidMax=10.0, Kp=20.000, Ki=0.600, Kd=-3.000, iMaxErr=0.500,
          idleRangeH=1.000, idleRangeL=-1.000, heatTargetH=0.301, heatTargetL=-0.199, coolTargetH=0.199,
          coolTargetL=-0.301, maxHeatTimeForEst="600", maxCoolTimeForEst="1200", fridgeFastFilt="1", fridgeSlowFilt="4",
          fridgeSlopeFilt="3", beerFastFilt="3", beerSlowFilt="5", beerSlopeFilt="4", lah=0, hs=0)

# Control variables
cv = dict(beerDiff=0.000, diffIntegral=0.000, beerSlope=0.000, p=0.000, i=0.000, d=0.000, estPeak=0.000,
          negPeakEst=0.000, posPeakEst=0.000, negPeak=0.000, posPeak=0.000)

# listState = "", "d", "h", "dh" to reflect whether the list is up to date for installed (d) and available (h)
deviceList = dict(listState="", installed=[], available=[])

lcdText = ['Script starting up', ' ', ' ', ' ']

# Read in command line arguments
try:
    opts, args = getopt.getopt(sys.argv[1:], "hc:sqkfld",
                               ['help', 'config=', 'status', 'quit', 'kill', 'force', 'log', 'dontrunfile', 'checkstartuponly'])
except getopt.GetoptError:
    printStdErr("Unknown parameter, available Options: --help, --config <path to config file>, " +
          "--status, --quit, --kill, --force, --log, --dontrunfile")
    sys.exit()

configFile = None
checkDontRunFile = False
checkStartupOnly = False
logToFiles = False

for o, a in opts:
    # print help message for command line options
    if o in ('-h', '--help'):
        printStdErr("\n Available command line options: ")
        printStdErr("--help: print this help message")
        printStdErr("--config <path to config file>: specify a config file to use. When omitted settings/config.cf is used")
        printStdErr("--status: check which scripts are already running")
        printStdErr("--quit: ask all  instances of BrewPi to quit by sending a message to their socket")
        printStdErr("--kill: kill all instances of BrewPi by sending SIGKILL")
        printStdErr("--force: Force quit/kill conflicting instances of BrewPi and keep this one")
        printStdErr("--log: redirect stderr and stdout to log files")
        printStdErr("--dontrunfile: check dontrunfile in www directory and quit if it exists")
        printStdErr("--checkstartuponly: exit after startup checks, return 1 if startup is allowed")
        exit()
    # supply a config file
    if o in ('-c', '--config'):
        configFile = os.path.abspath(a)
        if not os.path.exists(configFile):
            sys.exit('ERROR: Config file "%s" was not found!' % configFile)
    # send quit instruction to all running instances of BrewPi
    if o in ('-s', '--status'):
        allProcesses = BrewPiProcess.BrewPiProcesses()
        allProcesses.update()
        running = allProcesses.as_dict()
        if running:
            pprint(running)
        else:
            printStdErr("No BrewPi scripts running")
        exit()
    # quit/kill running instances, then keep this one
    if o in ('-q', '--quit'):
        logMessage("Asking all BrewPi Processes to quit on their socket")
        allProcesses = BrewPiProcess.BrewPiProcesses()
        allProcesses.quitAll()
        time.sleep(2)
        exit()
    # send SIGKILL to all running instances of BrewPi
    if o in ('-k', '--kill'):
        logMessage("Killing all BrewPi Processes")
        allProcesses = BrewPiProcess.BrewPiProcesses()
        allProcesses.killAll()
        exit()
    # close all existing instances of BrewPi by quit/kill and keep this one
    if o in ('-f', '--force'):
        logMessage("Closing all existing processes of BrewPi and keeping this one")
        allProcesses = BrewPiProcess.BrewPiProcesses()
        if len(allProcesses.update()) > 1:  # if I am not the only one running
            allProcesses.quitAll()
            time.sleep(2)
            if len(allProcesses.update()) > 1:
                printStdErr("Asking the other processes to quit nicely did not work. Killing them with force!")
    # redirect output of stderr and stdout to files in log directory
    if o in ('-l', '--log'):
        logToFiles = True
    # only start brewpi when the dontrunfile is not found
    if o in ('-d', '--dontrunfile'):
        checkDontRunFile = True
    if o in ('--checkstartuponly'):
        checkStartupOnly = True

if not configFile:
    configFile = util.addSlash(sys.path[0]) + 'settings/config.cfg'

config = util.readCfgWithDefaults(configFile)

dontRunFilePath = os.path.join(config['wwwPath'], 'do_not_run_brewpi')
# check dont run file when it exists and exit it it does
if checkDontRunFile:
    if os.path.exists(dontRunFilePath):
        # do not print anything, this will flood the logs
        exit(0)

# check for other running instances of BrewPi that will cause conflicts with this instance
allProcesses = BrewPiProcess.BrewPiProcesses()
allProcesses.update()
myProcess = allProcesses.me()
if allProcesses.findConflicts(myProcess):
    if not checkDontRunFile:
        logMessage("Another instance of BrewPi is already running, which will conflict with this instance. " +
                   "This instance will exit")
    exit(0)

if checkStartupOnly:
    exit(1)

localJsonFileName = ""
localCsvFileName = ""
wwwJsonFileName = ""
wwwCsvFileName = ""
lastDay = ""
day = ""

if logToFiles:
    logPath = util.addSlash(util.scriptPath()) + 'logs/'
    logMessage("Redirecting output to log files in %s, output will not be shown in console" % logPath)
    sys.stderr = open(logPath + 'stderr.txt', 'a', 0)  # append to stderr file, unbuffered
    sys.stdout = open(logPath + 'stdout.txt', 'w', 0)  # overwrite stdout file on script start, unbuffered


# userSettings.json is a copy of some of the settings that are needed by the web server.
# This allows the web server to load properly, even when the script is not running.
def changeWwwSetting(settingName, value):
    wwwSettingsFileName = util.addSlash(config['wwwPath']) + 'userSettings.json'
    if os.path.exists(wwwSettingsFileName):
        wwwSettingsFile = open(wwwSettingsFileName, 'r+b')
        try:
            wwwSettings = json.load(wwwSettingsFile)  # read existing settings
        except json.JSONDecodeError:
            logMessage("Error in decoding userSettings.json, creating new empty json file")
            wwwSettings = {}  # start with a fresh file when the json is corrupt.
    else:
        wwwSettingsFile = open(wwwSettingsFileName, 'w+b')  # create new file
        wwwSettings = {}

    wwwSettings[settingName] = str(value)
    wwwSettingsFile.seek(0)
    wwwSettingsFile.write(json.dumps(wwwSettings))
    wwwSettingsFile.truncate()
    wwwSettingsFile.close()

def setFiles():
    global config
    global localJsonFileName
    global localCsvFileName
    global wwwJsonFileName
    global wwwCsvFileName
    global lastDay
    global day

    # create directory for the data if it does not exist
    beerFileName = config['beerName']
    dataPath = util.addSlash(util.addSlash(util.scriptPath()) + 'data/' + beerFileName)
    wwwDataPath = util.addSlash(util.addSlash(config['wwwPath']) + 'data/' + beerFileName)

    if not os.path.exists(dataPath):
        os.makedirs(dataPath)
        os.chmod(dataPath, 0775)  # give group all permissions
    if not os.path.exists(wwwDataPath):
        os.makedirs(wwwDataPath)
        os.chmod(wwwDataPath, 0775)  # give group all permissions

    # Keep track of day and make new data file for each day
    day = time.strftime("%Y-%m-%d")
    lastDay = day
    # define a JSON file to store the data
    jsonFileName = beerFileName + '-' + day

    #if a file for today already existed, add suffix
    if os.path.isfile(dataPath + jsonFileName + '.json'):
        i = 1
        while os.path.isfile(dataPath + jsonFileName + '-' + str(i) + '.json'):
            i += 1
        jsonFileName = jsonFileName + '-' + str(i)

    localJsonFileName = dataPath + jsonFileName + '.json'
    brewpiJson.newEmptyFile(localJsonFileName)

    # Define a location on the web server to copy the file to after it is written
    wwwJsonFileName = wwwDataPath + jsonFileName + '.json'

    # Define a CSV file to store the data as CSV (might be useful one day)
    localCsvFileName = (dataPath + beerFileName + '.csv')
    wwwCsvFileName = (wwwDataPath + beerFileName + '.csv')

    # create new empty json file
    brewpiJson.newEmptyFile(localJsonFileName)

def startBeer(beerName):
    if config['dataLogging'] == 'active':
        setFiles()

    changeWwwSetting('beerName', beerName)


def startNewBrew(newName):
    global config
    if len(newName) > 1:     # shorter names are probably invalid
        config = util.configSet(configFile, 'beerName', newName)
        config = util.configSet(configFile, 'dataLogging', 'active')
        startBeer(newName)
        logMessage("Notification: Restarted logging for beer '%s'." % newName)
        return {'status': 0, 'statusMessage': "Successfully switched to new brew '%s'. " % urllib.unquote(newName) +
                                              "Please reload the page."}
    else:
        return {'status': 1, 'statusMessage': "Invalid new brew name '%s', "
                                              "please enter a name with at least 2 characters" % urllib.unquote(newName)}


def stopLogging():
    global config
    logMessage("Stopped data logging, as requested in web interface. " +
               "BrewPi will continue to control temperatures, but will not log any data.")
    config = util.configSet(configFile, 'beerName', None)
    config = util.configSet(configFile, 'dataLogging', 'stopped')
    changeWwwSetting('beerName', None)
    return {'status': 0, 'statusMessage': "Successfully stopped logging"}


def pauseLogging():
    global config
    logMessage("Paused logging data, as requested in web interface. " +
               "BrewPi will continue to control temperatures, but will not log any data until resumed.")
    if config['dataLogging'] == 'active':
        config = util.configSet(configFile, 'dataLogging', 'paused')
        return {'status': 0, 'statusMessage': "Successfully paused logging."}
    else:
        return {'status': 1, 'statusMessage': "Logging already paused or stopped."}


def resumeLogging():
    global config
    logMessage("Continued logging data, as requested in web interface.")
    if config['dataLogging'] == 'paused':
        config = util.configSet(configFile, 'dataLogging', 'active')
        return {'status': 0, 'statusMessage': "Successfully continued logging."}
    else:
        return {'status': 1, 'statusMessage': "Logging was not paused."}

# bytes are read from nonblocking serial into this buffer and processed when the buffer contains a full line.
ser = util.setupSerial(config, time_out=0)

if not ser:
    exit(1)

logMessage("Notification: Script started for beer '" + urllib.unquote(config['beerName']) + "'")
# wait for 10 seconds to allow an Uno to reboot (in case an Uno is being used)
time.sleep(float(config.get('startupDelay', 10)))


logMessage("Checking software version on controller... ")
hwVersion = brewpiVersion.getVersionFromSerial(ser)
if hwVersion is None:
    logMessage("Warning: Cannot receive version number from controller. " +
               "Your controller is either not programmed or running a very old version of BrewPi. " +
               "Please upload a new version of BrewPi to your controller.")
    # script will continue so you can at least program the controller
    lcdText = ['Could not receive', 'version from controller', 'Please (re)program', 'your controller']
else:
    logMessage("Found " + hwVersion.toExtendedString() + \
               " on port " + ser.name + "\n")
    if LooseVersion( hwVersion.toString() ) < LooseVersion(compatibleHwVersion):
        logMessage("Warning: minimum BrewPi version compatible with this script is " +
                   compatibleHwVersion +
                   " but version number received is " + hwVersion.toString())
    if int(hwVersion.log) != int(expandLogMessage.getVersion()):
        logMessage("Warning: version number of local copy of logMessages.h " +
                   "does not match log version number received from controller." +
                   "controller version = " + str(hwVersion.log) +
                   ", local copy version = " + str(expandLogMessage.getVersion()))

bg_ser = None

if ser is not None:
    ser.flush()

    # set up background serial processing, which will continuously read data from serial and put whole lines in a queue
    bg_ser = BackGroundSerial(ser)
    bg_ser.start()
    # request settings from controller, processed later when reply is received
    bg_ser.write('s')  # request control settings cs
    bg_ser.write('c')  # request control constants cc
    # answer from controller is received asynchronously later.

# create a listening socket to communicate with PHP
is_windows = sys.platform.startswith('win')
useInetSocket = bool(config.get('useInetSocket', is_windows))
if useInetSocket:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    socketPort = config.get('socketPort', 6332)
    s.bind((config.get('socketHost', 'localhost'), int(socketPort)))
    logMessage('Bound to TCP socket on port %d ' % int(socketPort))
else:
    socketFile = util.addSlash(util.scriptPath()) + 'BEERSOCKET'
    if os.path.exists(socketFile):
    # if socket already exists, remove it
        os.remove(socketFile)
    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(socketFile)  # Bind BEERSOCKET
    # set all permissions for socket
    os.chmod(socketFile, 0777)

serialCheckInterval = 0.5
s.setblocking(1)  # set socket functions to be blocking
s.listen(10)  # Create a backlog queue for up to 10 connections
# blocking socket functions wait 'serialCheckInterval' seconds
s.settimeout(serialCheckInterval)


prevDataTime = 0.0  # keep track of time between new data requests
prevTimeOut = time.time()
prevLcdUpdate = time.time()
prevSettingsUpdate = time.time()

run = 1

startBeer(config['beerName'])
outputTemperature = True

prevTempJson = {
    "BeerTemp": 0,
    "FridgeTemp": 0,
    "BeerAnn": None,
    "FridgeAnn": None,
    "RoomTemp": None,
    "State": None,
    "BeerSet": 0,
    "FridgeSet": 0}

def renameTempKey(key):
    rename = {
        "bt": "BeerTemp",
        "bs": "BeerSet",
        "ba": "BeerAnn",
        "ft": "FridgeTemp",
        "fs": "FridgeSet",
        "fa": "FridgeAnn",
        "rt": "RoomTemp",
        "s": "State",
        "t": "Time"}
    return rename.get(key, key)

while run:
    if config['dataLogging'] == 'active':
        # Check whether it is a new day
        lastDay = day
        day = time.strftime("%Y-%m-%d")
        if lastDay != day:
            logMessage("Notification: New day, creating new JSON file.")
            setFiles()

    # Wait for incoming socket connections.
    # When nothing is received, socket.timeout will be raised after
    # serialCheckInterval seconds. Serial receive will be done then.
    # When messages are expected on serial, the timeout is raised 'manually'
    try:
        conn, addr = s.accept()
        conn.setblocking(1)
        # blocking receive, times out in serialCheckInterval
        message = conn.recv(4096)
        if "=" in message:
            messageType, value = message.split("=", 1)
        else:
            messageType = message
            value = ""
        if messageType == "ack":  # acknowledge request
            conn.send('ack')
        elif messageType == "lcd":  # lcd contents requested
            conn.send(json.dumps(lcdText))
        elif messageType == "getMode":  # echo cs['mode'] setting
            conn.send(cs['mode'])
        elif messageType == "getFridge":  # echo fridge temperature setting
            conn.send(json.dumps(cs['fridgeSet']))
        elif messageType == "getBeer":  # echo fridge temperature setting
            conn.send(json.dumps(cs['beerSet']))
        elif messageType == "getControlConstants":
            conn.send(json.dumps(cc))
        elif messageType == "getControlSettings":
            if cs['mode'] == "p":
                profileFile = util.addSlash(util.scriptPath()) + 'settings/tempProfile.csv'
                with file(profileFile, 'r') as prof:
                    cs['profile'] = prof.readline().split(",")[-1].rstrip("\n")
            cs['dataLogging'] = config['dataLogging']
            conn.send(json.dumps(cs))
        elif messageType == "getControlVariables":
            conn.send(json.dumps(cv))
        elif messageType == "refreshControlConstants":
            bg_ser.write("c")
            raise socket.timeout
        elif messageType == "refreshControlSettings":
            bg_ser.write("s")
            raise socket.timeout
        elif messageType == "refreshControlVariables":
            bg_ser.write("v")
            raise socket.timeout
        elif messageType == "loadDefaultControlSettings":
            bg_ser.write("S")
            raise socket.timeout
        elif messageType == "loadDefaultControlConstants":
            bg_ser.write("C")
            raise socket.timeout
        elif messageType == "setBeer":  # new constant beer temperature received
            try:
                newTemp = float(value)
            except ValueError:
                logMessage("Cannot convert temperature '" + value + "' to float")
                continue
            if cc['tempSetMin'] <= newTemp <= cc['tempSetMax']:
                cs['mode'] = 'b'
                # round to 2 dec, python will otherwise produce 6.999999999
                cs['beerSet'] = round(newTemp, 2)
                bg_ser.write("j{mode:b, beerSet:" + json.dumps(cs['beerSet']) + "}")
                logMessage("Notification: Beer temperature set to " +
                           str(cs['beerSet']) +
                           " degrees in web interface")
                raise socket.timeout  # go to serial communication to update controller
            else:
                logMessage("Beer temperature setting " + str(newTemp) +
                           " is outside of allowed range " +
                           str(cc['tempSetMin']) + " - " + str(cc['tempSetMax']) +
                           ". These limits can be changed in advanced settings.")
        elif messageType == "setFridge":  # new constant fridge temperature received
            try:
                newTemp = float(value)
            except ValueError:
                logMessage("Cannot convert temperature '" + value + "' to float")
                continue

            if cc['tempSetMin'] <= newTemp <= cc['tempSetMax']:
                cs['mode'] = 'f'
                cs['fridgeSet'] = round(newTemp, 2)
                bg_ser.write("j{mode:f, fridgeSet:" + json.dumps(cs['fridgeSet']) + "}")
                logMessage("Notification: Fridge temperature set to " +
                           str(cs['fridgeSet']) +
                           " degrees in web interface")
                raise socket.timeout  # go to serial communication to update controller
            else:
                logMessage("Fridge temperature setting " + str(newTemp) +
                           " is outside of allowed range " +
                           str(cc['tempSetMin']) + " - " + str(cc['tempSetMax']) +
                           ". These limits can be changed in advanced settings.")
        elif messageType == "setOff":  # cs['mode'] set to OFF
            cs['mode'] = 'o'
            bg_ser.write("j{mode:o}")
            logMessage("Notification: Temperature control disabled")
            raise socket.timeout
        elif messageType == "setParameters":
            # receive JSON key:value pairs to set parameters on the controller
            try:
                decoded = json.loads(value)
                bg_ser.write("j" + json.dumps(decoded))
                if 'tempFormat' in decoded:
                    changeWwwSetting('tempFormat', decoded['tempFormat'])  # change in web interface settings too.
            except json.JSONDecodeError:
                logMessage("Error: invalid JSON parameter string received: " + value)
            raise socket.timeout
        elif messageType == "stopScript":  # exit instruction received. Stop script.
            # voluntary shutdown.
            # write a file to prevent the cron job from restarting the script
            logMessage("stopScript message received on socket. " +
                       "Stopping script and writing dontrunfile to prevent automatic restart")
            run = 0
            dontrunfile = open(dontRunFilePath, "w")
            dontrunfile.write("1")
            dontrunfile.close()
            continue
        elif messageType == "quit":  # quit instruction received. Probably sent by another brewpi script instance
            logMessage("quit message received on socket. Stopping script.")
            run = 0
            # Leave dontrunfile alone.
            # This instruction is meant to restart the script or replace it with another instance.
            continue
        elif messageType == "eraseLogs":
            # erase the log files for stderr and stdout
            open(util.scriptPath() + '/logs/stderr.txt', 'wb').close()
            open(util.scriptPath() + '/logs/stdout.txt', 'wb').close()
            logMessage("Fresh start! Log files erased.")
            continue
        elif messageType == "interval":  # new interval received
            newInterval = int(value)
            if 5 < newInterval < 5000:
                try:
                    config = util.configSet(configFile, 'interval', float(newInterval))
                except ValueError:
                    logMessage("Cannot convert interval '" + value + "' to float")
                    continue
                logMessage("Notification: Interval changed to " +
                           str(newInterval) + " seconds")
        elif messageType == "startNewBrew":  # new beer name
            newName = value
            result = startNewBrew(newName)
            conn.send(json.dumps(result))
        elif messageType == "pauseLogging":
            result = pauseLogging()
            conn.send(json.dumps(result))
        elif messageType == "stopLogging":
            result = stopLogging()
            conn.send(json.dumps(result))
        elif messageType == "resumeLogging":
            result = resumeLogging()
            conn.send(json.dumps(result))
        elif messageType == "dateTimeFormatDisplay":
            config = util.configSet(configFile, 'dateTimeFormatDisplay', value)
            changeWwwSetting('dateTimeFormatDisplay', value)
            logMessage("Changing date format config setting: " + value)
        elif messageType == "setActiveProfile":
            # copy the profile CSV file to the working directory
            logMessage("Setting profile '%s' as active profile" % value)
            config = util.configSet(configFile, 'profileName', value)
            changeWwwSetting('profileName', value)
            profileSrcFile = util.addSlash(config['wwwPath']) + "data/profiles/" + value + ".csv"
            profileDestFile = util.addSlash(util.scriptPath()) + 'settings/tempProfile.csv'
            profileDestFileOld = profileDestFile + '.old'
            try:
                if os.path.isfile(profileDestFile):
                    if os.path.isfile(profileDestFileOld):
                        os.remove(profileDestFileOld)
                    os.rename(profileDestFile, profileDestFileOld)
                shutil.copy(profileSrcFile, profileDestFile)
                # for now, store profile name in header row (in an additional column)
                with file(profileDestFile, 'r') as original:
                    line1 = original.readline().rstrip("\n")
                    rest = original.read()
                with file(profileDestFile, 'w') as modified:
                    modified.write(line1 + "," + value + "\n" + rest)
            except IOError as e:  # catch all exceptions and report back an error
                error = "I/O Error(%d) updating profile: %s " % (e.errno, e.strerror)
                conn.send(error)
                printStdErr(error)
            else:
                conn.send("Profile successfully updated")
                if cs['mode'] is not 'p':
                    cs['mode'] = 'p'
                    bg_ser.write("j{mode:p}")
                    logMessage("Notification: Profile mode enabled")
                    raise socket.timeout  # go to serial communication to update controller
        elif messageType == "programController" or messageType == "programArduino":
            if bg_ser is not None:
                bg_ser.stop()
            if ser is not None:
                if ser.isOpen():
                    ser.close()  # close serial port before programming
                ser = None
            try:
                programParameters = json.loads(value)
                hexFile = programParameters['fileName']
                boardType = programParameters['boardType']
                restoreSettings = programParameters['restoreSettings']
                restoreDevices = programParameters['restoreDevices']
                programmer.programController(config, boardType, hexFile, None, None, False,
                                          {'settings': restoreSettings, 'devices': restoreDevices})
                logMessage("New program uploaded to controller, script will restart")
            except json.JSONDecodeError:
                logMessage("Error: cannot decode programming parameters: " + value)
                logMessage("Restarting script without programming.")

            # restart the script when done. This replaces this process with the new one
            time.sleep(5)  # give the controller time to reboot
            python = sys.executable
            os.execl(python, python, *sys.argv)
        elif messageType == "refreshDeviceList":
            deviceList['listState'] = ""  # invalidate local copy
            if value.find("readValues") != -1:
                bg_ser.write("d{r:1}")  # request installed devices
                bg_ser.write("h{u:-1,v:1}")  # request available, but not installed devices
            else:
                bg_ser.write("d{}")  # request installed devices
                bg_ser.write("h{u:-1}")  # request available, but not installed devices
        elif messageType == "getDeviceList":
            if deviceList['listState'] in ["dh", "hd"]:
                response = dict(board=hwVersion.board,
                                shield=hwVersion.shield,
                                deviceList=deviceList,
                                pinList=pinList.getPinList(hwVersion.board, hwVersion.shield))
                conn.send(json.dumps(response))
            else:
                conn.send("device-list-not-up-to-date")
        elif messageType == "applyDevice":
            try:
                configStringJson = json.loads(value)  # load as JSON to check syntax
            except json.JSONDecodeError:
                logMessage("Error: invalid JSON parameter string received: " + value)
                continue
            bg_ser.write("U" + json.dumps(configStringJson))
            deviceList['listState'] = ""  # invalidate local copy
        elif messageType == "getVersion":
            if hwVersion:
                response = hwVersion.__dict__
                # replace LooseVersion with string, because it is not JSON serializable
                response['version'] = hwVersion.toString()
            else:
                response = {}
            response_str = json.dumps(response)
            conn.send(response_str)
        elif messageType == "resetController":
            logMessage("Resetting controller to factory defaults")
            bg_ser.write("E")
        else:
            logMessage("Error: Received invalid message on socket: " + message)

        if (time.time() - prevTimeOut) < serialCheckInterval:
            continue
        else:
            # raise exception to check serial for data immediately
            raise socket.timeout

    except socket.timeout:
        # Do serial communication and update settings every SerialCheckInterval
        prevTimeOut = time.time()

        if hwVersion is None:
            continue  # do nothing with the serial port when the controller has not been recognized

        if(time.time() - prevLcdUpdate) > 5:
            # request new LCD text
            prevLcdUpdate += 5 # give the controller some time to respond
            bg_ser.write('l')

        if(time.time() - prevSettingsUpdate) > 60:
            # Request Settings from controller to stay up to date
            # Controller should send updates on changes, this is a periodical update to ensure it is up to date
            prevSettingsUpdate += 5 # give the controller some time to respond
            bg_ser.write('s')

        # if no new data has been received for serialRequestInteval seconds
        if (time.time() - prevDataTime) >= float(config['interval']):
            bg_ser.write("t")  # request new from controller
            prevDataTime += 5 # give the controller some time to respond to prevent requesting twice

        elif (time.time() - prevDataTime) > float(config['interval']) + 2 * float(config['interval']):
            #something is wrong: controller is not responding to data requests
            logMessage("Error: controller is not responding to new data requests")


        while True:
            line = bg_ser.read_line()
            message = bg_ser.read_message()
            if line is None and message is None:
                break
            if line is not None:
                try:
                    if line[0] == 'T':
                        # print it to stdout
                        if outputTemperature:
                            print(time.strftime("%b %d %Y %H:%M:%S  ") + line[2:])

                        # store time of last new data for interval check
                        prevDataTime = time.time()

                        if config['dataLogging'] == 'paused' or config['dataLogging'] == 'stopped':
                            continue  # skip if logging is paused or stopped

                        # process temperature line
                        newData = json.loads(line[2:])
                        # copy/rename keys
                        for key in newData:
                            prevTempJson[renameTempKey(key)] = newData[key]

                        newRow = prevTempJson
                        # add to JSON file
                        brewpiJson.addRow(localJsonFileName, newRow)
                        # copy to www dir.
                        # Do not write directly to www dir to prevent blocking www file.
                        shutil.copyfile(localJsonFileName, wwwJsonFileName)
                        #write csv file too
                        csvFile = open(localCsvFileName, "a")
                        try:
                            lineToWrite = (time.strftime("%b %d %Y %H:%M:%S;") +
                                           json.dumps(newRow['BeerTemp']) + ';' +
                                           json.dumps(newRow['BeerSet']) + ';' +
                                           json.dumps(newRow['BeerAnn']) + ';' +
                                           json.dumps(newRow['FridgeTemp']) + ';' +
                                           json.dumps(newRow['FridgeSet']) + ';' +
                                           json.dumps(newRow['FridgeAnn']) + ';' +
                                           json.dumps(newRow['State']) + ';' +
                                           json.dumps(newRow['RoomTemp']) + '\n')
                            csvFile.write(lineToWrite)
                        except KeyError, e:
                            logMessage("KeyError in line from controller: %s" % str(e))

                        csvFile.close()
                        shutil.copyfile(localCsvFileName, wwwCsvFileName)
                    elif line[0] == 'D':
                        # debug message received, should already been filtered out, but print anyway here.
                        logMessage("Finding a log message here should not be possible, report to the devs!")
                        logMessage("Line received was: {0}".format(line))
                    elif line[0] == 'L':
                        # lcd content received
                        prevLcdUpdate = time.time()
                        lcdText = json.loads(line[2:])
                    elif line[0] == 'C':
                        # Control constants received
                        cc = json.loads(line[2:])
                    elif line[0] == 'S':
                        # Control settings received
                        prevSettingsUpdate = time.time()
                        cs = json.loads(line[2:])
                    # do not print this to the log file. This is requested continuously.
                    elif line[0] == 'V':
                        # Control settings received
                        cv = json.loads(line[2:])
                    elif line[0] == 'N':
                        pass  # version number received. Do nothing, just ignore
                    elif line[0] == 'h':
                        deviceList['available'] = json.loads(line[2:])
                        oldListState = deviceList['listState']
                        deviceList['listState'] = oldListState.strip('h') + "h"
                        logMessage("Available devices received: "+ json.dumps(deviceList['available']))
                    elif line[0] == 'd':
                        deviceList['installed'] = json.loads(line[2:])
                        oldListState = deviceList['listState']
                        deviceList['listState'] = oldListState.strip('d') + "d"
                        logMessage("Installed devices received: " + json.dumps(deviceList['installed']).encode('utf-8'))
                    elif line[0] == 'U':
                        logMessage("Device updated to: " + line[2:])
                    else:
                        logMessage("Cannot process line from controller: " + line)
                    # end or processing a line
                except json.decoder.JSONDecodeError, e:
                    logMessage("JSON decode error: %s" % str(e))
                    logMessage("Line received was: " + line)

            if message is not None:
                try:
                    expandedMessage = expandLogMessage.expandLogMessage(message)
                    logMessage("Controller debug message: " + expandedMessage)
                except Exception, e:  # catch all exceptions, because out of date file could cause errors
                    logMessage("Error while expanding log message '" + message + "'" + str(e))

        # Check for update from temperature profile
        if cs['mode'] == 'p':
            newTemp = temperatureProfile.getNewTemp(util.scriptPath())
            if newTemp != cs['beerSet']:
                cs['beerSet'] = newTemp
                # if temperature has to be updated send settings to controller
                bg_ser.write("j{beerSet:" + json.dumps(cs['beerSet']) + "}")

    except socket.error as e:
        logMessage("Socket error(%d): %s" % (e.errno, e.strerror))
        traceback.print_exc()

if bg_ser:
    bg_ser.stop()

if ser:
    if ser.isOpen():
        ser.close()  # close port
if conn:
    conn.shutdown(socket.SHUT_RDWR)  # close socket
    conn.close()

