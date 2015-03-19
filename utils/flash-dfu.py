# Copyright 2015 BrewPi
# This file is part of BrewPi.

# BrewPi is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# BrewPi is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with BrewPi.  If not, see <http://www.gnu.org/licenses/>.

import sys
# Check needed software dependencies to nudge users to fix their setup
if sys.version_info < (2, 7):
    print "Sorry, requires Python 2.7."
    sys.exit(1)

# standard libraries
import time
import socket
import os
import getopt
from pprint import pprint
import shutil
import traceback
import urllib
import subprocess

# Read in command line arguments
try:
    opts, args = getopt.getopt(sys.argv[1:], "hf:m",
                               ['help', 'file=', 'multi'])
except getopt.GetoptError:
    print "Unknown parameter, available Options: --file, --multi"

    sys.exit()

multi = False
binFile = None

for o, a in opts:
    # print help message for command line options
    if o in ('-h', '--help'):
        print "\n Available command line options: "
        print "--help: print this help message"
        print "--file: path to .bin file to flash"
        print "--multi: keep the script alive to flash multiple devices"
        exit()
    # supply a config file
    if o in ('-f', '--config'):
        binFile = os.path.abspath(a)
        if not os.path.exists(binFile):
            sys.exit('ERROR: Binary file "%s" was not found!' % binFile)
    # send quit instruction to all running instances of BrewPi
    if o in ('-m', '--multi'):
        multi = True
        print "Started in multi flash mode"

# check whether dfu-util can be found
if sys.platform.startswith('win'):
    p = subprocess.Popen("where dfu-util", stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
else:
    p = subprocess.Popen("which dfu-util", stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
p.wait()
output, errors = p.communicate()
if not output:
    print "dfu-util cannot be found, please add its location to your PATH variable"
    exit(1)

while(True):
    # list DFU devices to see whether a device is connected
    p = subprocess.Popen("dfu-util -l", stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    p.wait()
    output, errors = p.communicate()
    if errors:
        print errors
    if "Found" in output:
        # found a DFU device, flash the binary file to it
        if binFile:
            print "found DFU device, now flashing %s \n\n" % binFile

            p = subprocess.Popen("dfu-util -d 1d50:607f -a 0 -s 0x08005000:leave -D %s" % binFile, shell=True)
            p.wait()
        else:
            print "found DFU device, but no binary specified for flashing"
        if not multi:
            break

    time.sleep(1)
