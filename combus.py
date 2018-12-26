#!/usr/bin/python2.7
#
# (C) Kirils Solovjovs, 2015-2018
#
# Decodes paradox COMBUS protocol
# Input: lists of bytes in lowercase hex

def crc(data,s,x):
	x+=len(data)
	sum=-int(data[x],16)
	for i in range(s,x):
		sum+=int(data[i],16)
	return not (sum % 0x100)
	
def bcd(binary):
	r=""
	for sym in binary:
		for val in (sym >> 4, sym & 0xf):
			if val==0:
				return r
			r=r+str(val%10) #amazing "encryption"
	return r

def parse_source(data):
	if(data[0:2]=="00"):
		return "slave"
	else:
		return "master"
	
def parse_master_hello(data):
	if data[0]==0x7b:
		return str(data[3])
	else:
		return str(data[0]/0x10)

def parse_slave_code_entered(data):
	ctype='unknown'
	if data[3]==0x80: ctype='programmer'
	if data[3]==0: ctype='user'
	
	if data[6]==0xff or data[6]==0x01: #code follows
		code=bcd(data[7:13])
	else:
		code=""
			
	return "**"+code+"** for "+ctype+" from device #"+("%02X%02X%02X%02X" % tuple(data[13:17]))
	

def parse_slave_hello(data):
	return str(data[3])
	
def parse_master_time(data):
	if data[1]%2:
		time = "          %02i:%02i" % (data[2]-1,data[3]-1)
	else:
		time = "%2i day %02i:     " % (data[2],data[3]-1)
	return "%s   seqence #%03d"%(time,data[1])

def parse_labeltype(l):
	status=['user','zone','door','partition','area','module']
	
	if l>len(status) or not status[l]:
		return 'unknown'
	else:
		return status[l]
	

def parse_master_label(data):
	if(data[2]):
		return "_start"

	return parse_labeltype(data[1])+" #"+str(data[3]+1)+" \""+''.join(chr(i) for i in data[5:21])+"\""


def parse_master_event(data):
	stat=""
	stat+="A" if data[4] & 0x80 else "_" #alarms in memory
	stat+="T" if data[4] & 0x40 else "_" #troubles in memory
	stat+="Z" if data[4] & 0x20 else "_" #all zones ready
	# data[2], data[3] ??
	return "(%i day %02i:%02i) [%s] " % (data[3],data[4] & 0x1f , data[5], stat) + parse_event(data[6],data[8])+" in area #"+str(data[7])
	


def parse_event(group,subgroup):
	status=['closed zone #%d','opened zone #%d','tampered zone #%d','fireloop trouble zone #%d','other','user code #%d entered',
	'user #%d access on door','bypass programming by user #%d','tx delay alarm zone #%d','master #%d arming','user #%d arming',
	'keyswitch #%d arming','special_arm','master #%d disarming','user #%d disarming','keyswitch #%d disarming',
	'master #%d disarming (after alarm)','user #%d disarming (after alarm)','keyswitch #%d disarming (after alarm)',
	'master #%d disarming (alarm cancel)','user #%d disarming (alarm cancel)','keyswitch #%d disarming (alarm cancel)','special_disarm',
	'bypass zone #%d','ALARM zone #%d','FIRE ALARM zone #%d','was (alarm) zone #%d','was (fire alarm) zone #%d',
	'user #%d early to disarm','user #%d late to disarm by user','special_alarm','user #%d duress', 
	'shutdown zone #%d','tamper zone #%d','was (tamper) zone #%d','special_tamper',
	'trouble event','trouble restored','module trouble','module restored','phone #%d unreachable','low battery zone #%d',
	'supervision trouble zone #%d','battery ok zone #%d','supervision ok zone #%d','special_event',
	'user #%d early arm','user #%d late arm','utility key #%d','request for exit at door #%d','access denied at door #%d',
	'left open door #%d','forced door #%d','closed door #%d','unforced door #%d','trigger intellizone #%d','force arm excluding zone #%d',
	'return to arm zone #%d','new combus module #%d','lost combus module #%d','*future use*','*future use*','user #%d access granted','user #%d access denied',
	#3 more events (statuses) remaining
	]
	if group>=len(status) or not status[group]:
		return 'unknown'
	else:
		if "%" in status[group]:
			return status[group] % subgroup
		else:
			if 'parse_event_'+status[group].split(" ")[0] in globals():
				return (status[group])+" "+globals()['parse_event_'+status[group].split(" ")[0]](subgroup)
			else:
				return (status[group])+" (not implemented)"
	
def parse_event_other(subgroup):
	status=['tlm trouble','smoke detector reset','arm with no delay','arm in stay','arm in away','full arm in stay',
	'voice access','remote control access','pc fail','midnight','neware login','neware logout','user callup','force answer','force hangup','',
	'aux manual act','aux manual dis','voice fail','ftc restore','software access','ipr 1','ipr 2','ipr 3','ipr 4']
	
	if subgroup>len(status) or not status[subgroup]:
		return 'unknown'
	else:
		return status[subgroup]
	

def parse_event_special_arm(subgroup):
	status=['auto','winload','late to close','no movement','partial','one touch','','','voice']
	
	if subgroup>len(status) or not status[subgroup]:
		return 'unknown'
	else:
		return status[subgroup]

def parse_event_trouble(subgroup):
	hardware=['TLM','ac failure','battery failure','aux current overlimit','bell current overlimit','no bell found','clock trouble','global fire loop']
	hardware = { i : hardware[i] for i in range(0, len(hardware) ) }
	return hardware.get(subgroup) or 'unknown'

def parse_event_module(subgroup):
	hardware=['combus','tamper','memory','TLM','comm fail','printer','ac','battery','aux']
	hardware = { i : hardware[i] for i in range(0, len(hardware) ) }
	return hardware.get(subgroup) or 'unknonw'
	
def parse_special_event(subgroup):
	status=['cold boot','watchdog reset','test report','*future use*','winload connected','winload disconnected','installer in programming','installer done programming']
	status = { i : status[i] for i in range(0, len(status) ) }
	return status.get(subgroup) or 'unknown'

def parse_master_result(data):
	bits = ["denied" , "b1" ,"b2","b3","b4","b5","b6","b7"]
	result=[]
	for bitpos,res in enumerate(bits):
		if data[3] & (0x80>>bitpos): result.append(res)

	return ("accepted " if not "denied" in result else "")+" ".join(result)

def parse_event_special_tamper(subgroup):
	status=['keypad lockout','voice lockout']
	
	if subgroup>len(status) or not status[subgroup]:
		return 'unknown'
	else:
		return status[subgroup]


def parse_event_special_disarm(subgroup):
	status=['auto cancel','one touch','winload','winload (after alarm)','winload cancel','','','','voice']
	
	if subgroup>len(status) or not status[subgroup]:
		return 'unknown'
	else:
		return status[subgroup]


def parse_event_special_alarm(subgroup):
	status=['PANIC:emergency','PANIC:medical','PANIC:fire','recent closing','police code','zone shutdown','','',
	'TLM','comm failure','module tamper',
	'gsm missing','gsm no service','missing ip','ip no service','voice missing']
	
	if subgroup>len(status) or not status[subgroup]:
		return 'unknown'
	else:
		return status[subgroup]

def parse_master_remote(subgroup):
	buttons={
	1: 'lock',
	2: 'left',
	3: 'right',
	128: 'unlock',
	129: 'info',
	}
	return "button %s pressed for user #%i" % (buttons.get(subgroup[7]).upper() or "#"+str(subgroup[7]),subgroup[3])

def parse_slave_remote(subgroup):
	return parse_master_remote(subgroup)


def parse_master(data):
	cmdbyte = { 
	'0c': 'time', '0d': 'time', 
	'b0': 'label', 
	'e0': 'event', 'e1': 'event', 'e2': 'event', 'e3': 'event', 'e4': 'event', 'e5': 'event', 'e6': 'event', 'e7': 'event', 'e8': 'event', 'e9': 'event', 'ea': 'event', 'eb': 'event', 'ec': 'event', 'ed': 'event', 'ee': 'event', 'ef': 'event', 
	'11': 'hello', '21':'hello','31':'hello',
	'40': 'result',
	'71': 'remote',
	'7b': 'hello',
	}
	if not data[0] in cmdbyte:
		return 'command unknown'
	else:
		if 'parse_master_'+cmdbyte[data[0]] in globals():
			try:
				return (cmdbyte[data[0]])+" "+globals()['parse_master_'+cmdbyte[data[0]]]([int(each,16) for each in data])
			except: return 'command error'
		else:
			return (cmdbyte[data[0]])+" (not implemented)"


def parse_slave(data):
	cmdbyte = { '00': 'hello', '02':'request', '20':'code_entered', '24':'remote'}
	
	if len(data)<2:
		return 'command error'
		
	if data[1]=='00':
		return 'silence';
		
	if data[1]=='02':
		if not data[2] in cmdbyte:
			return 'command unknown'
		else:
			if 'parse_slave_'+cmdbyte[data[2]] in globals():
				try:
					return (cmdbyte[data[2]])+" "+globals()['parse_slave_'+cmdbyte[data[2]]]([int(each,16) for each in data])
				except: return 'command error'
			else:
				return (cmdbyte[data[2]])+" (not implemented)"	

	return 'command unknown'
