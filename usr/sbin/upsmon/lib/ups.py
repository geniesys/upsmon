# Global vars, shared functions, etc.

import socket, time, json, sys, os, getopt, re
import config

global VERBOSE
VERBOSE = None

###################################################################
# Socket connector wrapper. Return socket or None if can't connect.
###################################################################
def connect(HOST, PORT=3551):
	s   = None
	msg = None

	for res in socket.getaddrinfo(HOST, PORT, socket.AF_UNSPEC, socket.SOCK_STREAM):
	    #print res
	    #print socket.getaddrinfo(HOST, PORT, 0, 0, socket.IPPROTO_TCP)

	    af, socktype, proto, canonname, sa = res

	    try:
	        log('T','Creating socket')
	        s = socket.socket(af, socktype, proto)
	        s.settimeout(15)
	    except socket.error as msg:
	        log('E','Unable to create socket. ' + str(msg))
	        s = None
	        continue

	    try:
	        log('T','Connecting to %s:%s' % sa )
	        s.connect(sa)                # or s.connect((HOST, PORT))
	    except socket.error as msg:
	        log('D',str(msg) )
	        s.close()
	        s = None
	        continue
	    break

	return (s, sa, msg)

################## Try to detect type of remote host  ###################
def gethosttype(s):
	s.sendall('\x0006'+'status')
	s.setblocking(0)			# make socket non blocking
	time.sleep(0.25)
	data = s.recv(1024)			# receive response
	s.setblocking(1)			# make socket blocking again
	if data != '': return 'APC'

	s.sendall('HELP\n')
	s.setblocking(0)			# make socket non blocking
	time.sleep(0.25)
	data = s.recv(1024)			# receive response
	s.setblocking(1)			# make socket blocking again
	if data != '': return 'NUT'

	return 'Unknown'

###################################################################
# Socket receiver wrapper - Combines multiple data chunks received
# from the network into one complete piece and returns it.
###################################################################
def recvall(s,timeout=2):
	d='';						# combined data
	b='';						# intermediate buffer
	begin=time.time()				# remember beginning time

	s.setblocking(0)				# make socket non blocking

	while 1:
		if d and time.time()-begin > timeout:	# if we got some data, then break after timeout
		   break
		elif time.time()-begin > timeout*2:	# if we got no data at all, wait twice longer, then break
		   break

		try:
			b = s.recv(8192)		# receive something
			if b:
			   d += b

			   # When last 2 bytes of data equal null+null (could be the only two bytes received) or last line
			   # starts with 'END LIST' then exit loop without waiting for timeout - makes communications faster.

			   if b[-2:]=='\x00\x00' or b[b[:-1].rfind('\n')+1:-1][:8] == 'END LIST':
			      break

			   begin = time.time()		# update the beginning time

			else:
			   time.sleep(0.1)		# sleep for sometime to indicate a gap
		except:
			pass

	s.setblocking(1)				# make socket blocking again
	return d


##########################################################################
# Dump all collected information to specified output file or stdout.
# The data is in JSON format.
##########################################################################
def dump(UPS, outfile):
	if outfile is not None:
	   data = json.dumps(UPS, sort_keys=True, indent=2, separators=(',', ': '))
	   if outfile == '' or outfile == 'stdout':
	      print data
	   else:
	      fo = open(outfile, "wb")
	      fo.write(data)
	      fo.close()

# Log to file
def log(type, str):

	global logfile;
	global VERBOSE;

	if type in ['T','D'] and not VERBOSE: return	# Ignore Trace and Debug type messages when VERBOSE is off

	str = time.strftime("%Y-%m-%d %H:%M:%S") + ' ' + type + ' ' + str
	print str

	if logfile:
		fo = open(logfile, "a")
		fo.write( str + "\n")
		fo.close()

	return


##################### Process command line options and arguments #######################
def config(CONFIG):

	global VERBOSE
	global logfile	# need for log() function down below

	host, port, poll, user, pasw, outfile, logfile, cfgfile = CONFIG

	#print 'Number of CLI arguments:', len(sys.argv)
	#print 'Argument List:', str(sys.argv)

	try:
		opts, args = getopt.getopt(sys.argv[1:],'hvt:c:l:u:p:o:H:',['help','verbose','interval=','user=','pass=','cfg=','log=','out=','host='])
		#print opts
		#print args
	except getopt.GetoptError:
		log('E','Syntax error')
		help()
		sys.exit(2)

	for opt, arg in opts:

	    if opt in ('-h', '--help'):
		help()
		sys.exit(0)

	    elif opt in ('-v', '--verbose'):
		VERBOSE = True
		log('I','Verbose mode is ON')
		continue

	    elif opt in ('-t', '--interval'):
		poll = int(arg)
		continue

	    elif opt in ('-u', '--user'):
		user = arg
		continue

	    elif opt in ('-p', '--pass'):
		pasw = str(arg)
		continue

	    elif opt in ('-c', '--config', '--cfg', '--conf'):
		cfgfile = str(arg)
		log('I','Configuration file: ' + cfgfile + ' (not implemented)')
		continue

	    elif opt in ('-l', '--log'):
		logfile = str(arg)
		continue

	    elif opt in ('-o', '--out'):
		outfile = str(arg)
		log('I','Output file: ' + (outfile or 'stdout'))
		continue

	    elif opt in ('-H', '--host'):
		host = str(arg.split(':')[0])		# IP address of the remote host / upsd server
		port = int(arg.split(':')[1])		# Port number
		continue

	    else:
		log('W','Unexpected option ' + opt + '=' + str(arg) + ' - Ignored')

	for arg in args:
	    matchObj = re.match( r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}):?(\d{4,5})?', arg, re.M|re.I)
	    if matchObj:
	       host = str(matchObj.group(1))		# IP address of the remote host / upsd server
	       port = int(matchObj.group(2))		# port number
	       break

	    matchObj = re.match( r'([\w\.\-\_]+):?(\d{4,5})?', arg, re.M|re.I)
	    if matchObj:
	       host = str(matchObj.group(1))		# name of the remote host / upsd server
	       port = int(matchObj.group(2))		# port number
	       break

	if host is None:
	   log('I','Remote server address is not specified. Assuming localhost')
	   host = socket.gethostname()		# Assume local machine name

	if port is None:
	   log('I','Port number is not specified. Assuming 3551 (apcupsd)')
	   port = 3551				# Port on which remote upsd server listens. APC = 3551, NUT = 3493

	if poll is None:
	   poll = 30				# Polling interval between 10-60 sec. 30 sec recommended.

	if logfile is not None and logfile != '':
	   if logfile.find('/') == -1:		# if logfile does not contain path then assume the same directory where executable is located
	      logfile = os.path.realpath(os.path.dirname(os.path.realpath(__file__)) + '/../' + logfile)
	      log('I','Logfile file: ' + logfile)

	return (host, port, poll, user, pasw, outfile, logfile, cfgfile)

def help():
	print ''
	print 'Uninterruptable Power Supply Client'
	print ''
	print 'This program queries network-capable UPS device or software-based UPS server'
	print 'and allows to perform system shutdown or another user-defined actions when'
	print 'certain conditions exist.'
	print 'Currently supported software-based hosts: APCUPSD and NUT'
	print 'This program is not intended to work directly with USB-attached devices.'
	print ''
	print 'Syntax: upsc.py [options] <remote_hostname_or_ip>:<port>'
	print ' Where Options are:'
	print ' -h | --help			This help'
	print ' -v | --verbose			Verbose mode'
	print ' -t <sec>  | --interval=<sec>	Polling interval between 10 and 60 seconds. Default is 30 sec.'
	print ' -c <file> | -- cfg=<file>	Alternative configuration file.'
	print ' -l <file> | -- log=<file>	Log file. If path is not specified then directory where executable is located is assumed.'
	print ' -o <file> | -- out=<file>	Filename to dump collected data as JSON. stdout is assumed if filename is not specified.'
	print ' -u <str>  | --user=<str>	username (if your UPS require login)'
	print ' -p <str>  | --pass=<str>	password (if your UPS require login)'
	print ' -H <host:port> | --host=<host:port>	Alternative way to specify remote host.'
	print ''
