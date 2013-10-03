#!/bin/bash
# This bash script will update the CRON job that is used to start/restart/check BrewPi

############
### Functions to catch/display errors during setup
############
warn() {
  local fmt="$1"
  command shift 2>/dev/null
  echo -e "$fmt\n" "${@}"
  echo -e "\n*** ERROR ERROR ERROR ERROR ERROR ***\n----------------------------------\nSee above lines for error message\nScript NOT completed\n"
}

die () {
  local st="$?"
  warn "$@"
  exit "$st"
}

# the script path will one dir above the location of this bash file
unset CDPATH
myPath="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
scriptPath="$(dirname "$myPath")"

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
   rm /tmp/newcron||warn
   if ! ${firstLine}; then
       echo -e "Updated crontab to:"
       sudo crontab -u brewpi -l||die
       echo -e "Finished updating crontab"
   fi
fi
rm /tmp/oldcron||warn

echo -e "\ncopying new cron job to /etc/cron.d/brewpi"

if [[ "$scriptPath" != "/home/brewpi" ]]; then
    echo "Using non-default script path, using sed to write modified cron file to /etc/cron.d/brewpi"
    sudo sh -c "sed -e \"s,/home/brewpi,$scriptPath\",g $myPath/brewpi.cron > /etc/cron.d/brewpi"||die
else
    sudo cp "$myPath"/brewpi.cron /etc/cron.d/brewpi||die
fi


echo -e "Restarting cron"
sudo /etc/init.d/cron restart||die
