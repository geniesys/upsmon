import re
import lib.ups as ups
import lib.hexdump as hexdump

def request(sock, cmd):
	if ups.VERBOSE is not None: print '>', cmd
	sock.sendall( cmd + '\n')		# Send request
	response = sock.recv(64)		# Read response. Response will be 'BEGIN <cmd>\n'. It must be read from socket before the rest of the data is sent.
	if ups.VERBOSE is not None: print '<', response

	if response == 'BEGIN ' + cmd + '\n':
	   return response
	else:
	   return False


def parse_response(data):
	result = {}
	c = 0			# counter for items that should be enumerated

	for line in data.split('\n'):

	    if line      == ''   : continue
	    if line[0:3] == 'END': break

	    if line[0:6] == 'CLIENT':
		# Example: 'CLIENT ups 127.0.0.1'
		matchObj = re.match( r'CLIENT\s(\w+)\s(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})$', line, re.M|re.I)
	        if matchObj:
		   a = []		# must make it of the same type as other a's (array of object path keys)
	           a.append(c)		# for 'for k in a' below to work
		   c += 1		# and, in case of multiple clients, also enumerate them
	           v = matchObj.group(2)

	    elif line[0:3] == 'UPS':
		# Example: 'UPS ups "Description unavailable"'
	        matchObj = re.match( r'UPS\s([^\s]+)\s\"([^\"]+)\"$', line, re.M|re.I)
	        if matchObj:
		   a = []		# must make it of the same type as other a's (array of object path keys)
	           a.append(c)		# for 'for k in a' below to work
		   c += 1		# and, in case of multiple ups's (?), also enumerate them
	           v = {'id':matchObj.group(1), 'description':matchObj.group(2), 'type':'NUT'}

	    elif line[0:3] == 'CMD':
		# Example: 'CMD ups beeper.disable'
	        matchObj = re.match( r'CMD\s(\w+)\s([\w\.]+)$', line, re.M|re.I)
	        if matchObj:
	           a = matchObj.group(2).split('.')		# the dot-separated key path split into array
	           #v = None					# CMD LISTs do not have values
		   v = ''					# CMD LISTs do not have values

	    else:
	        matchObj = re.match( r'(\w+)\s(\w+)\s([\w\.]+)\s\"([^\"]+)\"$', line, re.M|re.I)
	        if matchObj:
	           a = matchObj.group(3).split('.')		# the dot-separated key path split into array
	           v = matchObj.group(4)			# the last quoted value

	    if not matchObj: continue

	    node = result

	    ####### This produces object where each value is a {'value': <value>} ##########
	    #for k in a:
	    #    node = node.setdefault(k, {})
	    #    if k == a[-1]:			# Last key
	    #      if node:
	    #         node = v
	    #      else:			# Not last key
	    #         node['value'] = v
	    ################################################################################

	    ################################################################################
	    # This produces more compact object where most of the leafs are {<key>: <value>}
	    # and only few (which had to be converted) are {'value': <value>}
	    ################################################################################
	    for k in a:
		if k == a[-1]:			# Last key?
		   node[k] = v
		else:				# k is not the last key in the chain
		    x = node.setdefault(k, {})			# if k already exists, this will return its value which could be something other than Dictionary object
		    if type(x) is not dict:			# the value of this node is not a Dictionary
		       node[k] = {'value': node[k]}		# convert it to Dictionary. Use 'value' as the name of the missing key
		       node = node[k]				# point variable node to this new node
		    else:					# the returned value is a Dictionary
		       node = x					# point variable node to this node

	return result
