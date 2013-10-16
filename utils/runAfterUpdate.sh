#!/bin/bash
# This script should be run after running the BrewPi updater. It will call 3 other bash scripts to:
# 1. Install required dependencies through apt-get
# 2. Update the BrewPi CRON job that starts/restarts the BrewPi python script
# 3. Fix the owner/permissions of the files in the web and script dir

# the script path will one dir above the location of this bash file
unset CDPATH
myPath="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

sudo bash "$myPath"/installDependencies.sh
sudo bash "$myPath"/updateCron.sh
sudo bash "$myPath"/fixPermissions.sh
