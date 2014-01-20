#!/bin/bash
### Wifi Checking/Re-Enabling script for Brewpi
### This checks every 10 minutes to see if the wifi connection is still active via a ping
### If not, it will re-enable the wlan0 interface
### Geo Van O, Jan 2014
### User-editable settings ###
# Total number of times to try and contact the router if first packet fails
MAX_FAILURES=3
# Time to wait between failed attempts contacting the router
INTERVAL=15
###  DO NOT EDIT BELOW HERE!  ###
DIR=$( cd "$( dirname "${BASH_SOURCE[0]}")" && pwd )

### Check if we have root privs to run
if [[ $EUID -ne 0 ]]; then
   echo "This script must be run as root: sudo ./wifiChecker.sh)" 1>&2
   exit 1
fi

if [ "$1" = "install" ]; then
    echo "Installing wifi checking script to /etc/cron.d/brewpi"
    ### Make sure auto wlan0 is added to /etc/network/interfaces, otherwise it causes trouble bringing the interface back up
    grep "auto wlan0" /etc/network/interfaces > /dev/null
    if [ $? -ne 0 ]; then
        printf '%s\n' 0a "auto wlan0" . w | ed -s /etc/network/interfaces
    fi

    ### Check if enableWlan is already added to cron file and, if not, add it
    grep "enableWlan.sh" /etc/cron.d/brewpi > /dev/null
    if [ $? -eq 0 ]; then
         echo "Cron entry already exists, skipping..."
    else
        ### Look at cron entry to find location of log files
        logPath=$(grep brewpi.py /etc/cron.d/brewpi|sed -r 's/.*(1>.*)$/\1/')|sed -r 's/>/>>/' >/dev/null
        echo "Adding cron job for Wifi checking to /etc/cron.d/brewpi"
        echo "*/10 * * * * $DIR/enableWlan.sh $logPath" >> /etc/cron.d/brewpi
    fi
    echo "Wifi checking script installed! No further action is needed."
    echo "You can run ./wifiChecker.sh from $DIR to manually test if you like."
    exit 0
fi

fails=0
gateway=$(/sbin/ip route | awk '/default/ { print $3 }')
### Sometimes network is so hosed, gateway IP is missing from ip route
if [ -z $gateway ]; then
    echo "BrewPi: wifiChecker: Cannot find gateway IP. Restarting wlan0 interface..." 1>&2
    /sbin/ifdown wlan0
    /sbin/ifup wlan0
    exit 0
fi

while [ $fails -lt $MAX_FAILURES ]; do
### Try pinging, and if host is up, exit
    ping -c 1 -I wlan0 $gateway > /dev/null
    if [ $? -eq 0 ]; then
        fails=0
        echo "BrewPi: wifiChecker: Successfully pinged $gateway"
        break
    fi
### If that didn't work...
    let fails=fails+1
    if [ $fails -lt $MAX_FAILURES ]; then
        echo "BrewPi: wifiChecker: Attempt $fails to reach $gateway failed" 1>&2
        sleep $INTERVAL
    fi
done

### Restart wlan0 interface
    if [ $fails -ge $MAX_FAILURES ]; then
        echo "BrewPi: wifiChecker: Unable to reach router. Restarting wlan0 interface..." 1>&2
        /sbin/ifdown wlan0
        /sbin/ifup wlan0
    fi

