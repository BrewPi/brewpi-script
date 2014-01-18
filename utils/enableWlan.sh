#!/bin/bash
### User-editable settings ###
# IP of the wifi router (Also known as your gateway IP)
ROUTER="192.168.1.1"
# Total number of times to try and contact the router if first packet fails
MAX_FAILURES=3
# Time to wait between failed attempts contacting the router
INTERVAL=15
###  DO NOT EDIT BELOW HERE!  ###

fails=0

while [ $fails -lt $MAX_FAILURES ]; do
### Try pinging, and if host is up, exit
    ping -c 1 -I wlan0 $ROUTER > /dev/null
    if [ $? -eq 0 ]; then
        fails=0
        echo "Successfully pinged $ROUTER"
        break
    fi
### If that didn't work...
    let fails=fails+1
    if [ $fails -lt $MAX_FAILURES ]; then
        echo "Attempt $fails to reach $ROUTER failed" 1>&2
        sleep $INTERVAL
    fi
done

### Restart wlan0 interface
    if [ $fails -ge $MAX_FAILURES ]; then
        echo "Unable to reach router. Restarting wlan0 interface..." 1>&2
        /sbin/ifup wlan0
    fi

