#!/bin/sh
PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/usr/local/games:/usr/games

if [ "$(ps ax | grep -v grep | grep brewpi.py)" != "" ]; then
    echo "brewpi running, everything is fine"
else
    if [ -f '/var/www/do_not_run_brewpi' ]; then
       echo "do_not_run_brewpi file exists, not restarting"
    else
        echo "brewpi not running, restarting brewpi"
        logger "brewpi script not found running by CRON, restarting brewpi"
        # overwrite stdout, append to stderr
        # -u flag causes stdout to write to file immediately and not cache output
        python -u /home/brewpi/brewpi.py 1> /home/brewpi/logs/stdout.txt 2>>/home/brewpi/logs/stderr.txt &
    fi
fi
exit 0

# if [ ! -f /dev/ttyACM0 ];
# then
#    echo "Serial port found"
# else
#    echo "Serial port not found, rebooting!"
#    logger Serial port not found, rebooting!
#    reboot
# fi

# This script checks whether the python script is running. If it is not running, it starts the script.
# A dontrun file is written if the script is stopped manually, so CRON will not restart it.
# A restart is logged to syslog