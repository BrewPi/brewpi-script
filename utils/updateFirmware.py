from __future__ import print_function
import sys
sys.path.append("..") # append parent directory to be able to import files

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
    family = None
    ser = None

    ### Get version number
    printStdErr("\nChecking current firmware version...")
    try:
        ser, conn = util.setupSerial(config)
        hwVersion = brewpiVersion.getVersionFromSerial(ser)
        family = hwVersion.family
        shield = hwVersion.shield
        board = hwVersion.board
    except:
        printStdErr("Unable to connect to controller, perhaps it is disconnected or otherwise unavailable")
        printStdErr("Please go to https://github.com/BrewPi/firmware/releases to download and upload via the BrewPi web interface")

    if ser:
        ser.close()  # close serial port
        ser = None

    if not hwVersion:
        printStdErr("Unable to retrieve firmware version from controller")
        return -1
    else:
        printStdErr("Current firmware version on controller: " + hwVersion.toString())

    printStdErr("\nChecking GitHub for latest release...")
    releases = gitHubReleases("https://api.github.com/repos/BrewPi/firmware")
    latest = releases.getLatestTag()
    printStdErr("Latest version on GitHub: " + latest)
    if hwVersion.isNewer(latest):
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
    if family == "Arduino":
        localFileName = releases.getBin(latest, [board, shield, ".hex"])
    elif family == "Spark":
        localFileName = releases.getBin(latest, [board, ".bin"])

    if localFileName:
        printStdErr("Latest firmware downloaded to " + localFileName)
    else:
        printStdErr("Downloading firmware failed")
        return -1

    result = programmer.programController(config, board, localFileName,
                                          {'settings': restoreSettings, 'devices': restoreDevices})
    util.removeDontRunFile(config['wwwPath'] + "/do_not_run_brewpi")
    return result

if __name__ == '__main__':
    result = updateFromGitHub(True)
    exit(result)