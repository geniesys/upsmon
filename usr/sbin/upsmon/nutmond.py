#!/usr/bin/python
#	^
#	You may need to adjust this path to your environment. Run "which python" to get the path.
#
######################################################################################
# General purpose UPS-NIS monitor and host "shutdowner" utility for Linux systems.
# This software is compatible with APCUPSD and NUT network information services (NIS).
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
	print 'Shutdown triggers:'
	print '	MIN_BAT_TIME =', config.MIN_BAT_TIME
	print '	MIN_BAT_PERC =', config.MIN_BAT_PERC

########### Try connecting to remote NIS service ##################################
s, sa, msg = ups.connect(HOST, PORT)
if s is None:
   print 'Cannot conect to %s:%s' % sa, msg
   sys.exit(1)	# terminate if unable to connect on startup - you must be able to connect before this script goes daemon.
else:
   s.close()

### We're good to go ###

print 'Connected to %s:%s' % sa

### Propagate certain internal variables into the UPS object (also for informational purposes)
UPS['type']     = 'NUT'
UPS['interval'] = POLL
UPS['DEVICES'].append({})


################## Begin Infinite Loop #######################
while True:

	###################### Connect/Reconnect #########################
	s, sa, msg = ups.connect(HOST, PORT)
	if s is None:
	    print 'Cannot conect to %s:%s' % sa, msg
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
	if ups.VERBOSE is not None: print '> VER'
	s.sendall('VER\n')
	data = s.recv(1024)			# receive response
	#print '<', data, len(data)
	UPS['version'] = data.rstrip()

	if ups.VERBOSE is not None: print '> NETVER'
	s.sendall('NETVER\n')
	data = s.recv(1024)			# receive response
	#print '<', data, len(data)
	UPS['netver'] = data.rstrip()

	######################## LOGIN (optional) ###########################
	# Sets the username and password associated with a connection.
	# This is also used for authentication, specifically in conjunction with the upsd.users file.
	# password is stored for commands that require it.
	#####################################################################
	if USER:   nut.request(s, 'USERNAME ' + USER)
	if PASS:   nut.request(s, 'PASSWORD ' + PASS)

	######################## Get available UPS's ########################
	# This must precede other commands. The UPS's id(s) obtained
	# here is/are used in the following queries.
	#####################################################################
	if nut.request(s, 'LIST UPS'):
	   data = ups.recvall(s);
	   devices = nut.parse_response(data)	# returns enumerated object that represents UPS devices being monitored by the parent service
	   #print devices

	   for i in devices:				# i is an integer because its enumerated object
	       # populate UPS['DEVICES'] array from 'devices' object. We're interested only in actual value of the 'value' properties of that object
	       # which is an object on its own. For example {'id': 'ups', 'description': 'Description unavailable'}
	       if devices[i].has_key('value'):
	          UPS['DEVICES'].append(devices[i]['value'])
	       else:
	          UPS['DEVICES'].append(devices[i])

	   devices, i = None, None

	######### Query each UPS device ###########
	for current_device in UPS['DEVICES']:	# DEVICES is an indexed array. 'current_device' is a Dictionary object.
	    id = current_device['id']

	    #nut.request(s, 'LOGIN '+id)  		# For master-slave operations. See doc. I'm unable to test any of this.

	    if nut.request(s, 'LIST VAR '+id):
	       data = ups.recvall(s);
	       node = current_device.setdefault('VAR', nut.parse_response(data) )

	    if nut.request(s, 'LIST RW '+id):
	       data = ups.recvall(s)
	       node = current_device.setdefault('RW', nut.parse_response(data) )

	    if nut.request(s, 'LIST CMD '+id):
	       data = ups.recvall(s)
	       data = 'CMD ups load.off\nCMD ups load.off.delay\nEND LIST CMD ups\n'	# TEMP. OVERRIDE
	       #print data
	       #print nut.parse_response(data)
	       node = current_device.setdefault('CMD', nut.parse_response(data) )

	    if nut.request(s, 'LIST CLIENT '+id):
	       data = ups.recvall(s)
	       #print data
	       node = current_device.setdefault('CLIENT', nut.parse_response(data) )

	    ################# Logout / Disconnect gracefully ################
	    #nut.request(s, 'LOGOUT')  		# For master-slave operations (?). I'm unable to test any of this.

	    ########### NOT IMPLEMENTED ############
	    # https://github.com/networkupstools/nut/blob/master/docs/net-protocol.txt
	    #
	    # GET NUMLOGINS <upsname>		GET NUMLOGINS su700			get the number of clients which have done LOGIN for this UPS. This is used by the master upsmon to determine how many clients are still connected when starting the shutdown process.
	    # GET UPSDESC <upsname>		GET UPSDESC su700			get the value of "desc=" from ups.conf for this UPS.  If it is not set, upsd will return "Unavailable".
	    # GET VAR <upsname> <varname>	GET VAR su700 ups.status		get single value
	    # GET TYPE <upsname> <varname>	GET TYPE su700 input.transfer.low	get type of a variable - RW, ENUM, STRING, RANGE, NUMBER
	    # GET DESC <upsname> <varname>	GET DESC su700 ups.status		get brief explanation of the named variable. upsd may return "Unavailable" if the file which provides this description is not installed.
	    # GET CMDDESC <upsname> <cmdname>	GET CMDDESC su700 load.on		similar to DESC above, but it applies to the instant commands.
	    # LIST ENUM <upsname> <varname>	LIST ENUM su700 input.transfer.low	
	    # LIST RANGE <upsname> <varname>	LIST RANGE su700 input.transfer.low
	    # SET VAR <upsname> <varname> "<value>"	SET VAR su700 ups.id "My UPS"
	    # INSTCMD <upsname> <cmdname>	INSTCMD su700 test.panel.start
	    # MASTER <upsname>		This function doesn't do much by itself. It is used by upsmon to make sure that master-level functions like FSD are available if necessary.
	    # FSD <upsname>		upsmon in master mode is the primary user of this function.  It sets this "forced shutdown" flag on any UPS when it plans to power it off.  This is done so that slave systems will know about it and shut down before the power disappears.
	    # STARTTLS

#	end of for loop

	##########################################################################
	# Dump all collected information to specified output file or stdout.
	# The data is in JSON format.
	##########################################################################
	if outfile is not None: ups.dump(UPS, outfile)


	######### Check each UPS device ###########
	for key, current_device in UPS['DEVICES'].iteritems():	# DEVICES is an indexed array. key is array's index. 'device' is a Dictionary object.

		################# Analyze UPS variables and trigger actions ##############
		current_device.['VAR']['battery']['charge' ]['value'] = '10.0'
		if SHUTDOWN_IN_PROGRESS:
		   if time.time() - SHUTDOWN_START_TIME > 600:
			# Target host (on which this daemon is running) has been shutting down for >10 minutes ?!
			# This process should have been dead by now, but it isn't. Something didn't work.
			# I better recover myself from shutdown mode and return to normal operations. 
			SHUTDOWN_IN_PROGRESS = False
		else:

		   if   float( current_device.['VAR']['battery']['runtime']['value'] ) / 60 <= config.MIN_BAT_TIME:	# example '4222' (in seconds) -> 4222/60 = 70 minutes
		      SHUTDOWN_IN_PROGRESS = True
		      print 'MIN_BAT_TIME condition is triggered. Remaining time is ' + str( float(UPS['DEVICES'][0]['VAR']['battery']['runtime']['value'])/60) + ' Minutes'

		   elif float( current_device.['VAR']['battery']['charge' ]['value'] ) <= config.MIN_BAT_PERC:	# example '100'
		      SHUTDOWN_IN_PROGRESS = True
		      print 'MIN_BAT_PERC condition is triggered. Remaining battery charge is ' + UPS['DEVICES'][0]['VAR']['battery']['charge' ]['value'] + '%'

		   if SHUTDOWN_IN_PROGRESS:
		      UPS['status'] = 'Shutting down host ...'
		      SHUTDOWN_START_TIME = time.time()
		      print subprocess.Popen('./shutdown.sh' + str(key) + ' ' + current_device['id']+'@'+HOST, shell=True)

#	end of for loop

	##########################################################################

	s.close()		# Close the socket when done

	if ups.VERBOSE is not None:
		print 'Sleeping for', POLL, 'seconds...'

	time.sleep(POLL)	# sleep for a while

# end of while loop