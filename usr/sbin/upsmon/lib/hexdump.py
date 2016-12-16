__version__ = '3.0'
__author__  = 'anatoly techtonik <techtonik@gmail.com>'
__license__ = 'Public Domain'

import binascii		# binascii is required for Python 3
import sys

# --- constants
PY3K = sys.version_info >= (3, 0)

# --- - chunking helpers
def chunks(seq, size):
	# Generator that cuts sequence (bytes, memoryview, etc.) into chunks of given size. If `seq` length is not multiply
	# of `size`, the lengh of the last chunk returned will be less than requested.
	# >>> list( chunks([1,2,3,4,5,6,7], 3) )	[[1, 2, 3], [4, 5, 6], [7]]

	d, m = divmod(len(seq), size)
	for i in range(d):
		yield seq[i*size:(i+1)*size]
	if m:
		yield seq[d*size:]

def chunkread(f, size):
	# Generator that reads from file like object. May return less data than requested on the last read.
	c = f.read(size)
	while len(c):
		yield c
		c = f.read(size)

def genchunks(mixed, size):
	# Generator to chunk binary sequences or file like objects. The size of the last chunk returned may be less than requested.
	if hasattr(mixed, 'read'):
		return chunkread(mixed, size)
	else:
		return chunks(mixed, size)

# --- - /chunking helpers

def dehex(hextext):
	# Convert from hex string to binary data stripping whitespaces from `hextext` if necessary.
	if PY3K:
		return bytes.fromhex(hextext)
	else:
		hextext = "".join(hextext.split())
		return hextext.decode('hex')

def dump(binary, size=2):
	# Convert binary data (bytes in Python 3 and str in Python 2) to hex string like '00 DE AD BE EF'.
	# `size` argument specifies length of text chunks.

	hexstr = binascii.hexlify(binary)
	if PY3K:
		hexstr = hexstr.decode('ascii')
	return ' '.join(chunks(hexstr.upper(), size))

def dumpgen(data):
	# Generator that produces strings:
	# '00000000: 00 00 00 00 00 00 00 00	00 00 00 00 00 00 00 00	................'
	generator = genchunks(data, 16)
	for addr, d in enumerate(generator):
		# 00000000:
		line = '%08X: ' % (addr*16)
		# 00 00 00 00 00 00 00 00	00 00 00 00 00 00 00 00 
		dumpstr = dump(d)
		line += dumpstr[:8*3]
		if len(d) > 8:	# insert separator if needed
			line += ' ' + dumpstr[8*3:]
		# ................
		# calculate indentation, which may be different for the last line
		pad = 2
		if len(d) < 16:	pad += 3*(16 - len(d))
		if len(d) <= 8:	pad += 1
		line += ' '*pad

		for byte in d:
			# printable ASCII range 0x20 to 0x7E

			if not PY3K:
				byte = ord(byte)

			if 0x20 <= byte <= 0x7E:
				line += chr(byte)
			else:
				line += '.'
		yield line

def hexdump(data, result='print'):
	# Transform binary data to the hex dump text format:
	# 00000000: 00 00 00 00 00 00 00 00	00 00 00 00 00 00 00 00	................
	# [x] data argument as a binary string
	# [x] data argument as a file like object
	#
	# Returns result depending on the `result` argument:
	# 'print'		 - prints line by line
	# 'return'		- returns single string
	# 'generator' - returns generator that produces lines

	if PY3K and type(data) == str:
		raise TypeError('Abstract unicode data (expected bytes sequence)')

	gen = dumpgen(data)
	if result == 'generator':
		return gen
	elif result == 'return':
		return '\n'.join(gen)
	elif result == 'print':
		for line in gen:
			print(line)
	else:
		raise ValueError('Unknown value of `result` argument')
