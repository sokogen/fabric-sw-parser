#!/usr/bin/python3
# -*- coding: utf-8 -*-
# Parcer FiberZone configures
# Author: Sokogen
import sys
from termcolor import colored, cprint

# Global parameters
portTableHeaders=('Index', 'Port', 'Address', 'Media', 'Speed', 'State', 'Proto', 'PortType', 'WWN', 'Other')
cgfkey='cfgshow'
portinfokey='portInfo'
swshkey='swshow'
fabshkey='fabSh'
primaryswkey='Primary'
AllWWNList=[]

#def ParceCfgShow(rawdata,
#				fabshkey=fabshkey):
#	""" Функция генерирует и возвращает многомерный словарь, содержащий:
#	вид конфига (defined, effective); тип объекта (cfg, zone, alias) и его имя;
#	и список значений для каждого из них. """
#	for line in rawdata[fabshkey]:
#		if 'Defined configuration:' in line:
#			definedstart = rawdata[host][cgfkey].index(line)
#			print ('definedstart: ',definedstart)
#		elif "Effective configuration:" in line:
#			effectivestart = rawdata[host][cgfkey].index(line)
#			print ('effectivestart: ', effectivestart)

#	for line in rawdata:
#		if "Defined configuration:" in line:
#			confType = "defined"
#			CfgDict[confType] = {}
#			continue
#		elif "Effective configuration:" in line:
#			confType = "effective"
#			CfgDict[confType] = {}
#			continue
#		elif len(line.split('\t')[0]) > 0 and len(line.split('\t')) == 3:
#			objectType = line.split('\t')[0].strip()[:-1]
#			objectName = line.split('\t')[1].strip()
#			objectValue = []
#			if len(line.split('\t')[2].strip()) > 0:
#				for value in line.split('\t')[2].split(';'):
#					objectValue.append(value.strip())
#			try:
#				CfgDict[confType][objectType][objectName] = []
#			except:
#				CfgDict[confType][objectType] = {}
#				CfgDict[confType][objectType][objectName] = []
#		elif len(line.split('\t')) == 3 and len(line.split('\t')[2].strip()) > 0:
#			objectValue = []
#			for value in line.split('\t')[2].split(';'):
#				if len(value.strip()) > 0:
#					objectValue.append(value.strip())
#			objectValue = tuple(objectValue)
#		else:
#			continue
#		CfgDict[confType][objectType][objectName].extend(objectValue)
#	return CfgDict

def ParceData(rawdata,
				swshkey=swshkey,
				portinfokey=portinfokey,
				portTableHeaders=portTableHeaders,
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
		for line in rawdata[host][swshkey][portstart + 1:]:
			line = line.split()
			while len(line) > len(portTableHeaders):
				line[-2] = line[-2] + ' ' + line[-1]
				line.pop()
			for row in range(len(line)):
				rowname = portTableHeaders[row]
				try:
					CommInfoDict[host][portinfokey][line[1]][rowname] = line[row]
				except:
					CommInfoDict[host][portinfokey][line[1]] = {}
					CommInfoDict[host][portinfokey][line[1]][rowname] = line[row]

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
	" It will return sorted list, which contained all WWNs. "
	primaryhosts=[]
	for each in list(infodict.keys()):
		ip=str(infodict[each]['switchPrimaryIP'])
		if ip not in primaryhosts:
			primaryhosts.append(ip)
	print (primaryhosts)
	AllWWNList=[]
	for host in primaryhosts:
		for value in infodict[host]['effCfg']['zone'].values():
			for each in value:
				if each not in AllWWNList:
					AllWWNList.append(each)

	AllWWNList=tuple(sorted(AllWWNList))
	print (AllWWNList)

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

	#	initialisation(sys.argv)
	rawdict = {}
	CommInfoDict = {}

#	fccommutators = """\
#	172.31.11.168,22,user1,Telegraph!
#	192.168.128.54,22,user,password"""

	fccommutators = """\
	172.31.11.168,22,user1,Telegraph!
	172.31.11.169,22,user1,Telegraph!
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
	GetAllWWN(CommInfoDict)

#	for fccommutator in fccommutators.split('\n'):
#		ipaddr = fccommutator.split(',')[0].split('\t')[-1].strip()
#		print("##############",ipaddr, "##############")
#		for key in (x for x in CommInfoDict[ipaddr] if x != portinfokey):
#			print (key, '=> ',CommInfoDict[ipaddr][key])
#		for key in (x for x in CommInfoDict[ipaddr] if x == portinfokey):
#			portlist=[]
#			info=CommInfoDict['172.31.11.168']['portInfo']
#			for port in range(len(list(info))):
#				oneportinfo=[]
#				for row in portTableHeaders:
#					try:
#						oneportinfo.append(info[str(port)][str(row)])
#					except:
#						oneportinfo.append('-')
#						continue
#				#	portlist[port].extend(info[port][row].values())
#				#print (tuple(oneportinfo))
#				portlist.append(tuple(oneportinfo))
#			for port in portlist:
#				print('{0:^3}|{1:^3}|{2:^8}|{3:^5}|{4:^4}|{5:^10}|{6:^4}|{7:^8}|{8:28}|{9:50}'.format(*port))

