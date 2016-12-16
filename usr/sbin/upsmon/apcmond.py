#!/usr/bin/env python
#	^
#	You may need to adjust this path to your environment. Run "which python" to get the path.
#
######################################################################################
# General purpose UPS-NIS monitor and host "shutdowner" utility for Linux systems.
# This software is compatible with APCUPSD and NUT Network Information Services (NIS).
# It is intended to monitor these services over the network and execute system
# shutdown when certain power conditions are reported by the monitored UPS device.
# This software works on ESXi 5.x, openSUSE 13.x, Ubuntu and should be compatible
# with many other Linux-based systems.
# This software does not work directly with USB- or RS232-connected UPS devices.
# 
# Copyright (c) 2016 Geniesys, Inc. (www.geniesys.net/upsmon)
# Author: Alex Dudnik
#
# Dual licensed under the MIT (MIT-LICENSE.txt) and GPL (GPL-LICENSE.txt) public
# licenses.
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
# INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
# PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#
# Free for commercial and non-commercial use.
# Please consider donating a few $$ to keep this and other projects going.
#
#  $Date: 2016-11-10 15:45:49 -0800 $
#  $Rev: 0001 $
#
# Files: apcmond.py, nutmond.py and related modules
# 
###################################################################################

import socket, sys, time, subprocess	# Import necessary modules
import lib.ups as ups			# Common functions in separate module
import lib.apc as apc			# APC-specific functions in separate module
import lib.nut as nut			# NUT-specific functions in separate module
import config				# Configuration file. Command-line arguments take higher priority.

########### Declare, reference, and set local and global variables ################
MIN_BAT_TIME = config.MIN_BAT_TIME or 10
MIN_BAT_PERC = config.MIN_BAT_PERC or 10
SHUTDOWN_IN_PROGRESS = False
SHUTDOWN_START_TIME  = None
UPS    = {'DEVICES':[]}			# stores all data from UPS monitoring service/daemon or network-enabled device being monitored.
CONFIG = (config.HOST, config.PORT, config.POLL, config.USER, config.PASS, config.outfile, config.logfile, config.cfgfile)

print ''

########### Process CLI parameters and update all listed variables ################
CONFIG = ups.config(CONFIG)
HOST, PORT, POLL, USER, PASS, outfile, logfile, cfgfile = CONFIG
CONFIG = None

########### Display certain values for informational purposes #####################
if ups.VERBOSE is not None:
	ups.log('T','Shutdown triggers: ' + \
		' MIN_BAT_TIME = ' + str(config.MIN_BAT_TIME) + ',' + \
		' MIN_BAT_PERC = ' + str(config.MIN_BAT_PERC) )

########### Try connecting to remote NIS service ##################################
s, sa, msg = ups.connect(HOST, PORT)
if s is None:
   ups.log('E','Cannot conect to %s:%s - ' % sa + str(msg))
   sys.exit(1)	# terminate if unable to connect on startup - you must be able to connect before this script goes daemon.
else:
   s.close()

### We're good to go ###

ups.log('I','Connected to %s:%s' % sa)

### Propagate certain internal variables into the UPS object (also for informational purposes)
UPS['type']     = 'APC'
UPS['interval'] = POLL
UPS['DEVICES'].append({})


################## Begin Infinite Loop #######################
while True:

	###################### Connect/Reconnect #########################
	s, sa, msg = ups.connect(HOST, PORT)
	if s is None:
	    ups.log('E','Cannot conect to %s:%s' % sa + str(msg))
	    UPS['status'] = 'Not Connected'
	    UPS['error']  = str(msg)
	    if outfile is not None: ups.dump(UPS, outfile)
	    time.sleep(POLL)
	    continue
	else:
	    UPS['host']   = '%s:%s' % sa
	    UPS['error']  = ''
	    if SHUTDOWN_IN_PROGRESS == False:
	       UPS['status'] = 'Connected'

	################ Re-Detect Remote Server Type  ##################
	#UPS['type'] = ups.gethosttype(s)		# but do it quietly

	###################### Start Talking ############################
	try:
		UPS['DEVICES'][0]['STATUS'] = apc.get_status(s)
	except:
		pass

	try:
		UPS['DEVICES'][0]['EVENTS'] = apc.get_events(s)
	except:
		pass

	##########################################################################
	# Dump all collected information to specified output file or stdout.
	# The data is in JSON format.
	##########################################################################
	if outfile is not None: ups.dump(UPS, outfile)

	##########################################################################
	# Analyze UPS variables and trigger actions.
	# It doesn't look like apcupsd is capable of monitoring multiple UPS's.
	# The 'DEVICES' collection will always contain only one device therefore
	# index is hardcoded to "0".
	##########################################################################
	if SHUTDOWN_IN_PROGRESS:
	   if time.time() - SHUTDOWN_START_TIME > 600:
		# Target host (on which this daemon is running) has been shutting down for >10 minutes ?!
		# This process should have been dead by now, but it isn't. Something didn't work.
		# I better recover myself from shutdown mode and return to normal operations. 
		SHUTDOWN_IN_PROGRESS = False
	else:

	   # Occasionaly, apc.get_status(s) fails to retrieve the data. Skip current evaluation cycle when this happens.
	   if len(UPS['DEVICES']) > 0 and \
	      UPS['DEVICES'][0].has_key('STATUS') and \
	      UPS['DEVICES'][0]['STATUS'].has_key('TIMELEFT'):

		# Determine which variable to use for minimum-battery-time comparison
		if str(config.MIN_BAT_TIME) == 'MINTIMEL':	# use ups's MINTIMEL value
		   MIN_BAT_TIME = float( UPS['DEVICES'][0]['STATUS']['MINTIMEL'].split(' ')[0] )		# example: '10 Minutes'
		else:						# use MIN_BAT_TIME value specified in config.py
		   MIN_BAT_TIME = float( config.MIN_BAT_TIME )	# this should alredy be specified as int or float

		# Determine which variable to use for minimum-battery-charge comparison
		if str(config.MIN_BAT_TIME) == 'MBATTCHG':	# use ups's MBATTCHG value
		   MIN_BAT_PERC = float( UPS['DEVICES'][0]['STATUS']['MBATTCHG'].split(' ')[0] )		# example: '10.0 Percent'
		else:						# use MIN_BAT_PERC value specified in config.py
		   MIN_BAT_PERC = float( config.MIN_BAT_PERC )	# this should alredy be specified as int or float


		# Now, compare 'current status' values against configured limits
		if   float( UPS['DEVICES'][0]['STATUS']['TIMELEFT'].split(' ')[0] ) <= MIN_BAT_TIME:		# example: '68.5 Minutes'
		     SHUTDOWN_IN_PROGRESS = True
		     ups.log('I','MIN_BAT_TIME condition is triggered. Remaining time is ' + UPS['DEVICES'][0]['STATUS']['TIMELEFT'])
		elif float( UPS['DEVICES'][0]['STATUS']['BCHARGE' ].split(' ')[0] ) <= MIN_BAT_PERC:		# example '100.0 Percent'
		     SHUTDOWN_IN_PROGRESS = True
		     ups.log('I','MIN_BAT_PERC condition is triggered. Remaining battery charge is ' + UPS['DEVICES'][0]['STATUS']['BCHARGE'])

		if SHUTDOWN_IN_PROGRESS:
		   # if this flag was raised, begin shutdown mode. This is done to prevent repeated execution of shutdown.sh
		   UPS['status'] = 'Shutting down host ...'	# set new ups status for informational purposes
		   SHUTDOWN_START_TIME = time.time()		# start tracking shutdown time in order to recover from unsuccessful shutdowns
		   print subprocess.Popen('./shutdown.sh 0 ups0@'+HOST, shell=True)

	   else:
		ups.log('T','UPS[DEVICES][0][STATUS][TIMELEFT] is not set')
		ups.log('T',str(UPS))
		pass

	#################################################################

	s.close()		# Close the socket when done

	ups.log('T','Sleeping for '+str(POLL)+' seconds...')

	time.sleep(POLL)	# sleep for a while

# end of while loop