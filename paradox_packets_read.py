#!/usr/bin/python2.7
#
# (C) Kirils Solovjovs, 2015-2018
#
# Decodes paradox COMBUS protocol
# Input: space-delimited hex
# Source: socket at 115200 baud

dev = "/dev/ttyACM3"
#logfile = "inputlog.txt"
squelch={'silence', 'time', 'hello'} #squelch common messages

import combus
import serial


s = serial.Serial(dev, 115200, timeout = 1)
line=""

#one empty reply to time command - things are stable now
while line.strip()!="00 00 00 00":
	line = s.readline()

print "Ready to process!"

while s:
	line = s.readline()
	if line.strip() == "":
		continue

	try:
		if logfile:
			with open(logfile, "a") as myfile:
				myfile.write(line)
	except: pass
	
	intext=line.lower().strip()
	
	source=combus.parse_source(intext)[0]
	command=intext.split(' ')
	prefix="<> "
	checksum=None
	if(source=='m'):
		prefix="-> "
		if len(command)>4:
			checksum="OK " if combus.crc(command,0,-2) else "ERR"
		try:
			parsed=combus.parse_master(command)
		except:
			parsed="packet error"

	elif(source=='s'):
		prefix="<- "
		if len(command)>12:
			checksum="OK " if combus.crc(command,2,-2) else "ERR"
		try:
			parsed=combus.parse_slave(command)
		except:
			parsed="packet error"

	else:
		parsed='source unknown'

	if not parsed.split(' ')[0] in squelch:
		if parsed=="command unknown":
			print prefix+"          "+parsed,"".join(command)
		else:
			print prefix+("[CRC="+checksum+"] " if checksum is not None else "          ")+parsed

