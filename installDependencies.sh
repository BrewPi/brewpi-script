#!/bin/bash
# Copyright 2013 BrewPi
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

########################
### This script will install dependencies required by BrewPi and will check/update the brewpi user's crontab
########################

############
### Functions to catch/display errors during setup
############
warn() {
  local fmt="$1"
  command shift 2>/dev/null
  echo -e "$fmt\n" "${@}"
  echo -e "\n*** ERROR ERROR ERROR ERROR ERROR ***\n----------------------------------\nSee above lines for error message\nSetup NOT completed\n"
}

die () {
  local st="$?"
  warn "$@"
  exit "$st"
}

############
### Install required packages
############
echo -e "\n***** Installing/updating required packages... *****\n"
#sudo apt-get update
#sudo apt-get install -y rpi-update apache2 libapache2-mod-php5 php5-cli php5-common php5-cgi php5 python-serial python-simplejson python-configobj python-psutil python-setuptools python-git python-gitdb python-setuptools arduino-core git-core||die

# the install path will be the location of this bash file
installPath="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

############
### Install Web Crontab
############
echo -e "\n***** Updating crontab for the brewpi user... *****\n"

newCronLine="* * * * * python -u $installPath/brewpi.py --dontrunfile 1>$installPath/logs/stdout.txt 2>>$installPath/logs/stderr.txt &"

sudo crontab -u brewpi -l > /tmp/tempcron
echo -e "Current crontab for user brewpi is:"
cat /tmp/tempcron
echo -e "\nThe updated CRON line for starting BrewPi is:\n$newCronLine \n"
read -p "Do you want to replace the entire crontab (r), append to the existing crontab (a) or skip this step (s)? [r]: " replaceOrAppend
if [ -z "$replaceOrAppend" ]; then
    replaceOrAppend="r"
fi;
case "$replaceOrAppend" in
    "r" | "R"  )
        echo "Replacing crontab with new line"
        sudo -u brewpi echo -e "$newCronLine"
        sudo -u brewpi echo -e "$newCronLine" > /tmp/tempcron||die||die
        sudo crontab -u brewpi /tmp/tempcron||die
        ;;
    "a" | "A"  )
        echo "Appending new line to crontab"
        sudo -u brewpi echo -e "$newCronLine" >> /tmp/tempcron||die||die
        sudo crontab -u brewpi /tmp/tempcron||die
        ;;
    "s" | "S"  )
        echo "Skipping crontab update"
        ;;
    *)
        echo -e "Invalid option, crontab not changed\n"
        ;;
esac
rm /tmp/tempcron||die

echo -e "\n***** Fixing file permissions, with sh $installPath/fixPremssions.sh *****\n"
sudo sh "$installPath"/fixPermissions.sh

echo -e "\n***** Done processing BrewPi dependencies *****\n"
