#!/bin/sh

#########################################################################
# This shell script is called by apcmond.py and nutmond.py
# when "shutdown" event is triggered.
#
# Every Linux system has a way to to be powered down from command line.
# A few examples provided below. Enable what you need. 
# You can further customize this script to fit your specific needs.
#
# Make sure this file has execute permissions - 'chmod 744 ./shutdown.sh'
#########################################################################

#########################################################################
# Most Linux systems
#########################################################################
# shutdown [OPTIONS...] [TIME] [WALL...]
#
#     --help      Show this help
#  -H --halt      Halt the machine
#  -P --poweroff  Power-off the machine		<- THIS IS WHAT YOU WANT
#  -r --reboot    Reboot the machine
#  -h             Equivalent to --poweroff, overridden by --halt
#  -k             Don't halt/power-off/reboot, just send warnings
#     --no-wall   Don't send wall message before halt/power-off/reboot
#  -c             Cancel a pending shutdown
#
#shutdown -p


#########################################################################
# ESX 5.x system shutdown via esxcli
#########################################################################
#esxcli system shutdown

# Another ESX 5.x script (???)
#/usr/bin/host_shutdown.sh

