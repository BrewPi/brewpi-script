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
DIR=`pwd`

if [ "$1" = "install" ]; then
    echo "Installing wifi check/enable script..."
    gateway=$(/sbin/ip route | awk '/default/ { print $3 }')
    ### Make sure auto wlan0 is added to /etc/network/interfaces, otherwise it causes trouble bringing the interface back up
    grep "auto wlan0" /etc/network/interfaces
    if [ $? -ne 0 ]; then
        printf '%s\n' 0a "auto wlan0" . w | ed -s /etc/network/interfaces
    fi

    ### Check if enableWlan is already added to cron file and, if not, add it
    grep "enableWlan.sh" /etc/cron.d/brewpi
    if [ $? -eq 0 ]; then
         echo "Cron entry already exists, skipping..."
    else
        logPath=$(grep brewpi.py /etc/cron.d/brewpi|sed -r 's/.*(1>.*)$/\1/')
        echo "Installing cron job for Wifi checking..."
        echo "*/10 * * * * $DIR/enableWlan.sh $logPath" >> /etc/cron.d/brewpi
    fi
    echo "Wifi check script installed! No further action is needed."
    echo "You can run ./enablewifi.sh from this directory to manually test if you like."
    exit 0
fi

fails=0

while [ $fails -lt $MAX_FAILURES ]; do
### Try pinging, and if host is up, exit
    ping -c 1 -I wlan0 $gateway > /dev/null
    if [ $? -eq 0 ]; then
        fails=0
        echo "Successfully pinged $gateway"
        break
    fi
### If that didn't work...
    let fails=fails+1
    if [ $fails -lt $MAX_FAILURES ]; then
        echo "Attempt $fails to reach $gateway failed" 1>&2
        sleep $INTERVAL
    fi
done

### Restart wlan0 interface
    if [ $fails -ge $MAX_FAILURES ]; then
        echo "Unable to reach router. Restarting wlan0 interface..." 1>&2
        /sbin/ifup wlan0
    fi

