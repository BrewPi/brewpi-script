#!/bin/sh
PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/usr/local/games:/usr/games

uptime=$(cat /proc/uptime)
uptime=${uptime%%.*}

if [ $uptime -gt 5000 ]; then
    echo "long enough"
else
    echo "not long enough"
fi

echo "$uptime"

# This script checks whether the python script is running. If it is not running, it starts the script.
# A dontrun file is written if the script is stopped manually, so CRON will not restart it.
# When the Raspberry Pi has lost it's serial port, it will restart the pi.
