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
sudo apt-get update
sudo apt-get install -y rpi-update apache2 libapache2-mod-php5 php5-cli php5-common php5-cgi php5 python-serial python-simplejson python-configobj python-psutil python-setuptools python-git python-gitdb python-setuptools arduino-core git-core||die

# the install path will be the location of this bash file
unset CDPATH
installPath="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

############
### Install cron job
############
echo -e "\n***** Updating cron for the brewpi user... *****\n"

sudo crontab -u brewpi -l > /tmp/oldcron
if [ -s /tmp/oldcron ]; then
   > /tmp/newcron||die
   firstLine=true
   while read line
   do
       case "$line" in
           \#*) # just copy commented lines
           echo "$line" >> /tmp/newcron;
           continue ;;
           *)
           if ${firstLine} ; then
               echo -e "You have some entries in the brewpi user's crontab."
               echo -e "The cron job to start/restart brewpi has been moved to cron.d"
               echo -e "This means the lines for brewpi in the crontab are not needed anymore."
               echo -e "A menu will follow to ask you to keep or comment out each line. Most users will want to answer 'yes'"
               echo -e "Please choose what you want to do with the following entries in the crontab:\n"
               firstLine=false
           fi
           echo "crontab line: $line"
           read -p "Do you want to comment out this line? [Y/n]: " yn </dev/tty
           case "$yn" in
               y | Y | yes | YES| Yes ) echo "Commenting line"; echo "# $line" >> /tmp/newcron;;
               n | N | no | NO | No ) echo -e "Keeping original line\n"; echo "$line" >> /tmp/newcron;;
               * ) echo "No valid choice received, assuming yes..."; echo "Commenting line"; echo "# $line" >> /tmp/newcron;;
           esac
       esac
   done < /tmp/oldcron
   sudo crontab -u brewpi /tmp/newcron||die
   rm /tmp/newcron||die
   if ! ${firstLine}; then
       echo -e "Updated crontab to:"
       sudo crontab -u brewpi -l
       echo -e "Finished updating crontab"
   fi
fi
rm /tmp/oldcron||die
echo -e "\ncopying new cron job to /etc/cron.d/brewpi"
sudo cp "$installPath"/brewpi.cron /etc/cron.d/brewpi
echo -e "Restarting cron"
sudo /etc/init.d/cron restart



echo -e "\n***** Fixing file permissions, with 'sh $installPath/fixPermissions.sh' *****\n"
sudo sh "$installPath"/fixPermissions.sh

echo -e "\n***** Done processing BrewPi dependencies *****\n"
