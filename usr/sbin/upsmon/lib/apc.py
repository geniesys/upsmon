import time
import lib.ups as ups
import lib.hexdump as hexdump

def get_status(s):

	retries = 2

	for i in range(0,retries):

		ups.recvall(s,0.25)			# quick "read" to clear any data that might remain in socket buffer

		if ups.VERBOSE is not None: print '< status'
		s.sendall('\x00\x06'+'status')

		# if ups.VERBOSE is not None: print '---------- BLOCKLING MODE ---------------'
		# time.sleep(5)				# wait for a while - response is never ready right away. APCUPSD is especially slow.
		# data = s.recv(1024)			# blocking. Normal response size is about 980 bytes.

		# if ups.VERBOSE is not None: print '---------- NON-BLOCKLING MODE ---------------'
		time.sleep(0.5)				# wait for a while - response is never ready right away. APCUPSD is especially slow.
		data = ups.recvall(s,5)			# non-blocking receive with 5 sec. timeout

		if ups.VERBOSE is not None:
			print '---------- begin received data ---------------'
			hexdump.hexdump(data)
			print '---------- end received data   ---------------'

		if   len(data) >= 64:
		     break
		elif len(data) <  64:
		     if ups.VERBOSE is not None: print 'Received data is too short. Retrying...'
		     time.sleep(1)
		else:
		     if ups.VERBOSE is not None: print 'Nothing was received. Retrying...'
		     time.sleep(1)

	# end for loop

	if data == '': return {}			# get out of here if still no data

	result = {}

	for line in data.split('\x0A'):
	    #size = line[0:2]
	    line = line[2:]
	    if line      == ''   : continue
	    if line[0:3] == 'END': break
	    k = line[0:9].rstrip(' ')
	    v = line[11:].strip(' ')
	    if ups.VERBOSE is not None: print k + ' : ' + v
	    result[k] = v

	return result


def get_events(s):

	retries = 1

	for i in range(0,retries):

		ups.recvall(s,0.25)			# quick "read" to clear any data that might remain in socket buffer

		if ups.VERBOSE is not None: print '< events'
		s.sendall('\x00\x06'+'events')

		### BLOCKLING MODE ###
		# time.sleep(2)				# wait for a while - response is never ready right away. APCUPSD is especially slow.
		# data = s.recv(2048)			# blocking. Response size varies. When event log is empty, the response is 0x00 0x00.

		### NON-BLOCKLING MODE ###
		time.sleep(0.25)			# wait a while - response is never ready right away. APCUPSD is especially slow.
		data = ups.recvall(s,5)			# non-blocking receive with 5 sec. timeout

		if ups.VERBOSE is not None:
			print ' ---------- begin received data ---------------'
			hexdump.hexdump(data)
			print ' ---------- end received data   ---------------'

	# end for loop

	if len(data) < 18 : return {}	# everything less that 18 bytes (2-byte line size prefix + 16 bytes of data) is considered invalid

	result = {}
	c = 0

	for line in data.split('\x10'):
	    #size = line[0:2]
	    line = line[2:]
	    if line      == ''   : continue
	    if line[0:3] == 'END': break
	    if ups.VERBOSE is not None: print 'line =', line
	    result[c] = line
	    c += 1

	return result
