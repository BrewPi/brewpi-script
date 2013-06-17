#!/bin/bash
echo "check-runnign.sh has been repaced by process management in the script itself."
echo "The BrewPi script will now exit when another script is already running that would cause conflict."
echo "Please change your brewpi users crontab to just start the brewpi script:"
echo "sudo -u brewpi crontab -e"
echo "change the line to:  * * * * * python /home/brewpi/brewpi.py"

exit 0

# This file is deprecated and will be removed in a future release of brewpi.
