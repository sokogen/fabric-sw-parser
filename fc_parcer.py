#!/usr/bin/python3
# -*- coding: utf-8 -*-
# Parcer FiberZone configures
# Author: Sokogen
import sys

# Global parameters
portTableHeadersExp=['PortType', 'WWN', 'Port description']
AllportTableHeaders=['Area', 'Index', 'Port', 'Address', 'Media', 'Speed', 'State', 'Proto']+portTableHeadersExp
cgfkey='cfgShow'
portinfokey='portInfo'
swshkey='swShow'
fabshkey='fabSh'
primaryswkey='Primary'

def ParceData(rawdata,
				swshkey=swshkey,
				portinfokey=portinfokey,
				portTableHeadersExp=portTableHeadersExp,
				cgfkey=cgfkey,
				fabshkey=fabshkey,
				primaryswkey=primaryswkey
				):
	""" Функция получает на вход словарь с данными с устройств,
	генерирует и возвращает многомерный словарь, содержащий
	подробное описание портов свитча и общую информацию
	по каждому свитчу
	CommInfoDict	{ ip хоста 	{ headinfo + PrimarySwInfo
								{ portinfo		{portTableHeaders}
	"""
	for host in list(rawdata.keys()):

		# Collecting PrimarySwitch name/ip
		for line in rawdata[host][fabshkey][2:]:
			line = line.split()
			if line[5][:2] == '>"':
				primaryswip=line[3]
				primaryswname=line[5][2:-1]
				try:
					CommInfoDict[host]['switchPrimaryIP'] = str(primaryswip)
					CommInfoDict[host]['switchPrimaryName'] = str(primaryswname)
				except KeyError:
					CommInfoDict[host] = {}
					CommInfoDict[host]['switchPrimaryIP'] = str(primaryswip)
					CommInfoDict[host]['switchPrimaryName'] = str(primaryswname)
				break

		# Collecting "Head" arguments from 'switchshow' command 
		portstart = 0
		for line in rawdata[host][swshkey]:
			if line.count('=') > 10:
				portstart = rawdata[host][swshkey].index(line)

		for line in rawdata[host][swshkey][:portstart-2]:
			line = line.split('\t')
			argmnt, value = line[0][:-1], line[-1]
			try:
				CommInfoDict[host][argmnt] = str(value.strip())
			except KeyError:
				CommInfoDict[host] = {}
				CommInfoDict[host][argmnt] = str(value.strip())
		# Collecting info from ports table
		CommInfoDict[host][portinfokey]={}
		portTableHeaders=rawdata[host][swshkey][portstart-1].split()
		if portTableHeaders[0] == 'Area':			# Костыль для FabricOS
			portTableHeaders=portTableHeaders[:-1]	# 6 версии (пустые поля типа порта)
		portTableHeaders=portTableHeaders+portTableHeadersExp
		for line in rawdata[host][swshkey][portstart + 1:]:
			line = line.split()
			try:
				port = line[1]
			except:
				continue
			while len(line) > len(portTableHeaders):
				line[-2] = line[-2] + ' ' + line[-1]
				line.pop()
			for row in range(len(line)):
				rowname = portTableHeaders[row]
				if rowname == 'WWN':
					if line[row].count(':')<7:
						line[row+1]=line[row] + ' ' + line[row+1]
						continue
				try:
					CommInfoDict[host][portinfokey][port][rowname] = line[row]
				except:
					CommInfoDict[host][portinfokey][port] = {}
					CommInfoDict[host][portinfokey][port][rowname] = line[row]

		# Collecting config information from 'cfgshow' command 
		for line in rawdata[host][cgfkey]:
			if "Defined configuration:" in line:
				confType = 'defCfg'
				definedstart = rawdata[host][cgfkey].index(line)
				CommInfoDict[host][confType]={}
				continue
			elif "Effective configuration:" in line:
				confType = 'effCfg'
				effectivestart = rawdata[host][cgfkey].index(line)
				CommInfoDict[host][confType]={}
				continue
			line=line.split('\t')
			objectValue=[]
			if len(line) == 3 and len(line[0]) > 0:
				objectType=line[0].strip()[:-1]
				objectName=line[1].strip()
				try:
					CommInfoDict[host][confType][objectType][objectName] = []
				except:
					CommInfoDict[host][confType][objectType] = {}
					CommInfoDict[host][confType][objectType][objectName] = []
			if len(line) == 3 and len(line[2]) > 0:
				for value in line[2].split(';'):
						objectValue.append(value.strip())
			CommInfoDict[host][confType][objectType][objectName].extend(objectValue)


	return CommInfoDict

def GetAllWWN(infodict):
	" It returns the sorted tuple that contains all WWNs. "
	primaryhosts=[]
	for each in list(infodict.keys()):
		ip=str(infodict[each]['switchPrimaryIP'])
		if ip not in primaryhosts:
			primaryhosts.append(ip)
	AllWWNList=[]
	for host in primaryhosts:
		for value in infodict[host]['effCfg']['zone'].values():
			for each in value:
				if each not in AllWWNList:
					AllWWNList.append(each)

	AllWWNList=tuple(sorted(AllWWNList))

	return AllWWNList

def InfoAllWWN(deviceAddrList, confDict):
	" Associating all receved device addresses with all used zones and aliases. "

	for wwn in deviceAddrList:
		DevicesInfoDict[wwn] = {}

		DevicesInfoDict[wwn]['zone'] = []
		for zonename, value in confDict['effective']['zone'].items():
			if wwn in value:
				DevicesInfoDict[wwn]['zone'].append(zonename)

		DevicesInfoDict[wwn]['alias'] = []
		for zonename, value in confDict['defined']['alias'].items():
			if wwn in value:
				DevicesInfoDict[wwn]['alias'].append(zonename)

	return DevicesInfoDict

def InfoWWN(deviceAddr, confDict):
	" Associating one device address with all used zones and aliases. "
	DevicesInfo[deviceAddr] = {}

	DevicesInfo[deviceAddr]['zone'] = []
	for zonename, value in confDict['effective']['zone'].items():
		if deviceAddr in value:
			DevicesInfo[deviceAddr]['zone'].append(zonename)

	DevicesInfo[deviceAddr]['alias'] = []
	for zonename, value in confDict['defined']['alias'].items():
		if deviceAddr in value:
			DevicesInfo[deviceAddr]['alias'].append(zonename)

	return DevicesInfo

if __name__ == "__main__":

	import paramiko
	import operator

	rawdict = {}
	CommInfoDict = {}

	fccommutators = """\
	172.31.11.204,22,user,password
	172.31.11.205,22,user,password
	172.31.11.206,22,user,password
	172.31.11.207,22,user,password
	192.168.128.18,22,user,password
	192.168.128.19,22,user,password
	192.168.128.53,22,user,password
	192.168.128.54,22,user,password"""

	for fccommutator in fccommutators.split('\n'):
		ipaddr, port, username, password = fccommutator.split(',')
		ipaddr = ipaddr.split('\t')[-1].strip()
		if '192.168.128' in ipaddr:
			cfgfilename = ipaddr + '.cfgshow'
			swshfilename = ipaddr + '.switchshow'
			fabshfilename = ipaddr + '.fabsh'
			rawdict[ipaddr] = {cgfkey: [], swshkey: [], fabshkey: []}
			with open(cfgfilename, 'r') as cfg:
				rawdict[ipaddr][cgfkey].extend(line.rstrip('\n') for line in cfg)
			with open(swshfilename, 'r') as swsh:
				rawdict[ipaddr][swshkey].extend(line.rstrip('\n') for line in swsh)
			with open(fabshfilename, 'r') as fabsh:
				rawdict[ipaddr][fabshkey].extend(line.rstrip('\n') for line in fabsh)

			print (ipaddr,'> done')
			continue

		client = paramiko.SSHClient()
		client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
		client.connect(hostname=ipaddr, username=username, password=password.strip(), port=int(port))
		rawdict[ipaddr] = {}
		stdinCfg, stdoutCfg, stderrCfg = client.exec_command('cfgshow')
		rawdict[ipaddr][cgfkey] = stdoutCfg.read().decode('utf8').split('\n')
		stdinSwSh, stdoutSwSh, stderrSwSh = client.exec_command('switchshow')
		rawdict[ipaddr][swshkey] = stdoutSwSh.read().decode('utf8').split('\n')
		stdinFabSh, stdoutFabSh, stderrFabSh = client.exec_command('fabricshow')
		rawdict[ipaddr][fabshkey] = stdoutFabSh.read().decode('utf8').split('\n')
		client.close()
		print (ipaddr,'> done')

	ParceData(rawdict)

#	print (CommInfoDict)

	AllWWNList=GetAllWWN(CommInfoDict)

	if sys.argv[-1].lower() == 'csv':
	# Show information for all WWN
		print ('{0};{1};{2};{3}'.format('WWN','Switch port','Aliases','Zones'))
	else: print ('{0:^24}|{1:^40}|{2:^18}|{3:>5}'.format('WWN','Switch port','Aliases','Zones'))

	for wwn in AllWWNList:
		switchport,aliases,zones='-','None','None'
		for host in list(CommInfoDict.keys()):
			info=CommInfoDict[host]
			for port in info[portinfokey].keys():
				if wwn in info[portinfokey][port].values():
					switchport='SwitchName: '+str(info['switchName'])+' / Port: '+str(info[portinfokey][port]['Port'])
			for alias in (x for x in list(info['defCfg']['alias'].keys()) if x not in aliases):
				if wwn in info['defCfg']['alias'][alias] :
					try:
						aliases.append(alias)
					except:
						aliases=[]
						aliases.append(alias)
			for zone in (x for x in list(info['effCfg']['zone'].keys()) if x not in zones):
				if wwn in info['effCfg']['zone'][zone]:
					try:
						zones.append(zone)
					except:
						zones=[]
						zones.append(zone)

		if type(aliases) == list:
			aliases = ', '.join(aliases)
		if type(zones) == list:
			zones = ', '.join(zones)

		string=(wwn,switchport,aliases,zones)

		if sys.argv[-1].lower() == 'csv':
		# Clear csv
			print ('{0};{1};{2};{3}'.format(*string))
		else:
		# Formated
			print ('{0:24}|{1:<40}|{2:<18}|{3}'.format(*string))


	
	primaryhosts=[]
	for each in list(CommInfoDict.keys()):
		ip=str(CommInfoDict[each]['switchPrimaryIP'])
		if ip not in primaryhosts:
			primaryhosts.append(ip)
	for prhost in primaryhosts:
		prhostname=CommInfoDict[prhost]['switchPrimaryName']
		print ('\n\n','<'*10, 'Rules for PrimaryHost:',prhostname,'>'*10)
		for fccommutator in fccommutators.split('\n'):
			ipaddr = fccommutator.split(',')[0].split('\t')[-1].strip()
			info=CommInfoDict[ipaddr]
			if prhost not in CommInfoDict[ipaddr]['switchPrimaryIP']:
				continue
			print('\n\n','#'*7,' ',ipaddr,' ','#'*7)
			for key in (x for x in info if x not in (portinfokey,'defCfg','effCfg')):
				print (key, '=> ',info[key])
			for key in (x for x in info if x in (portinfokey)):
				portlist=[]
				for port in range(len(list(info[portinfokey]))):
					oneportinfo=[]
					aliases,zones='None','None'
					for row in AllportTableHeaders:
						try:
							oneportinfo.append(info[portinfokey][str(port)][str(row)])
						except:
							oneportinfo.append('-')
							continue
					if 'WWN' in list(info[portinfokey][str(port)].keys()):
						wwn = str(info[portinfokey][str(port)]['WWN'])
						for alias in list(info['defCfg']['alias'].keys()):
							if wwn in info['defCfg']['alias'][alias]:
								try:
									aliases.append(alias)
								except:
									aliases=[]
									aliases.append(alias)
						if type(aliases) == list:
							aliases = ', '.join(aliases)
						else: aliases = 'None'
						
						for zone in list(info['effCfg']['zone'].keys()):
							if wwn in info['effCfg']['zone'][zone]:
								try:
									zones.append(zone)
								except:
									zones=[]
									zones.append(zone)
						if type(zones) == list:
							zones = ', '.join(zones)
						else: zones = 'None'
					oneportinfo.append(aliases)
					oneportinfo.append(zones)
					portlist.append(tuple(oneportinfo))

				if sys.argv[-1].lower() == 'csv':
				# Clear csv
					print('{2};{4};{5};{6};{8};{9};{10};aliases;zones'.format(*AllportTableHeaders))
					for port in portlist:
						print('{2};{4};{5};{6};{8};{9};{10};{11};{12}'.format(*port))

				else:
				# Formated
				#	print('{0:^4}|{1:^5}|{2:^4}|{3:^7}|{4:^5}|{5:^5}|{6:^10}|{7:^5}|{8:^8}|{9:^23}|{10:^32}|aliases|zones'.format(*AllportTableHeaders))
				#	for port in portlist:
				#		print('{0:^4}|{1:^5}|{2:^4}|{3:^7}|{4:^5}|{5:^5}|{6:^10}|{7:^5}|{8:^8}|{9:23}|{10:32}|{11}|{12}'.format(*port))
					print('{2:^4}|{4:^5}|{5:^5}|{6:^10}|{8:^8}|{9:^23}|{10:^32}|aliases|zones'.format(*AllportTableHeaders))
					for port in portlist:
						print('{2:^4}|{4:^5}|{5:^5}|{6:^10}|{8:^8}|{9:23}|{10:32}|{11}|{12}'.format(*port))
	
		print('\n\n\n')

	print()
