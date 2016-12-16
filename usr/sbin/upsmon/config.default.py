#########################################################################
# Default Configuration file for UPS monitor.
# (!) Command-line arguments take higher priority.
#########################################################################
HOST = None			# IP address or name of the remote NIS server being monitored
PORT = None			# Port on which remote UPS-NIS server listens. APC = 3551 (default), NUT = 3493
POLL = None			# Polling interval in seconds. Value around 60 sec is recommended. Default 30 seconds.
USER = None			# Username (if your UPS require login)
PASS = None			# Password (if your UPS require login)
outfile = None			# Filename to dump collected data in JSON format. stdout is assumed if filename is '' (empty string). None to disable.
logfile = None			# Log file name. If path is not specified log is created in the same directory where executable script is located.
cfgfile = None			# Alternative configuration file (not implemented).

#########################################################################
# TRIGGERS
# UPS monitor will execute shutdown.sh when corresponding UPS's status
# variable is equal or less than any one of these values.
# Note that SmartUPS estimates this value based on current load. When
# host begins shutdown consumed power will rise.
#########################################################################

# Remaining Time on battery in minutes.
# Alternatively, SmartUPS users can use MIN_BAT_TIME = 'MINTIMEL' to refer
# to MINTIMEL parameter configured in UPS itself instead of this value.

MIN_BAT_TIME = 10

# Remaining Battery Charge percent (estimated by SmartUPS).
# Alternatively, SmartUPS users can use MIN_BAT_PERC = 'MBATTCHG' to refer
# to MBATTCHG parameter configured in UPS itself instead of this value.

MIN_BAT_PERC = 10  

#########################################################################
