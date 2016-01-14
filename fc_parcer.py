#!/usr/bin/python3
# Parcer FiberZone files
# Author: Sokogen
import json,sys

#fabricHost='172.31.11.204'
#fabricHostPort=22
#fabricHostUser='user'
#fabricHostPass='password'

def CheckArguments(argmnts):
	" Проверить синтаксис запроса. "
	if len(argmnts) == 1:
		print ("Add filename.", "\n" ,"\'parcer.py file_name\'")
		exit()
	elif len(argmnts) > 2:
		print ("Too many arguments.", "\n" ,"\'parcer.py one_file_name\'")
		exit()

def PrintAllData(rawdata):
	" Просто вывести все данные. "
	with open(rawdata, 'r', encoding='utf-8') as data:
		for line in data:
			print (line.split('\t'))

def ParceData(rawdata):
	""" Функция генерирует и возвращает многомерный словарь, содержащий:
	вид конфига (defined, effective); тип объекта (cfg, zone, alias) и его имя;
	и список значений для каждого из них. """

	with open(rawdata, 'r', encoding='utf-8') as data:
		for line in data:
			if "Defined configuration:" in line:
				confType="defined"
				fabricConfDict[confType]={}
				continue
			elif "Effective configuration:" in line:
				confType="effective"
				fabricConfDict[confType]={}
				continue
			elif len(line.split('\t')[0]) > 0 and len(line.split('\t')) == 3:
				objectType=line.split('\t')[0].strip()[:-1]
				objectName=line.split('\t')[1].strip()
				objectValue=[]
				if len(line.split('\t')[2].strip())>0:
					for value in line.split('\t')[2].split(';'):
						objectValue.append(value.strip())
				try:
					fabricConfDict[confType][objectType][objectName]=[]
				except:
					fabricConfDict[confType][objectType]={}
					fabricConfDict[confType][objectType][objectName]=[]
			elif len(line.split('\t')) == 3 and len(line.split('\t')[2].strip()) > 0:
				objectValue=[]
				for value in line.split('\t')[2].split(';'):
					if len(value.strip()) > 0:
						objectValue.append(value.strip())
			else:
				continue
			fabricConfDict[confType][objectType][objectName].extend(objectValue)

	return fabricConfDict

def GetAllWWN(confDict):
	" It will return sorted list, which contained all WWNs. "
	for zonename, value in confDict['effective']['zone'].items():
		for each in value:
			if each not in AllWWNList:
				AllWWNList.append(each)
	AllWWNList.sort()
	return AllWWNList

def InfoAllWWN(confDict):
	"  "
	WWNList=[]
	WWNInfoDict={}
	for wwn in WWNList:
		for zonename, value in confDict['effective']['zone'].items():
			if wwn in value:
				print (zonename)
				print ("value: ",value)
				print ("wwn:   ",wwn)
				try:
					WWNInfoDict[wwn]['zone'].append(zonename)
				except:
					WWNInfoDict[wwn]={}
					WWNInfoDict[wwn]['zone']=[]
					WWNInfoDict[wwn]['zone'].append(zonename)

	print (type(WWNInfoDict))
	return WWNInfoDict


def InfoWWN(deviceAddr, confDict):
	" Associating each device address used with all its zones and aliases. "
	DevicesInfo[deviceAddr]={}

	DevicesInfo[deviceAddr]['zone']=[]
	for zonename, value in confDict['effective']['zone'].items():
		if deviceAddr in value:
			DevicesInfo[deviceAddr]['zone'].append(zonename)

	DevicesInfo[deviceAddr]['alias']=[]
	for zonename, value in confDict['defined']['alias'].items():
		if deviceAddr in value:
			DevicesInfo[deviceAddr]['alias'].append(zonename)

	return DevicesInfo

if __name__ == "__main__":

	CheckArguments(sys.argv)

	fabricConfDict={}
	WWNInfoDict={}
	AllWWNList=[]
	DevicesInfo={}

	ParceData(sys.argv[1])
	GetAllWWN(fabricConfDict)
#	InfoAllWWN(fabricConfDict)

	for wwn in AllWWNList:
		InfoWWN(wwn, fabricConfDict)

	for wwn in AllWWNList:
		print ("\n", wwn, end="")

		print (";", end="")
		for zone in DevicesInfo[wwn]['zone'][:-1]:
			print (zone, end=", ")
		print (DevicesInfo[wwn]['zone'][-1], end="")

		print (";", end="")
		if len(DevicesInfo[wwn]['alias']) > 0:
			for alias in DevicesInfo[wwn]['alias'][:-1]:
				print (alias, end="")
			print (DevicesInfo[wwn]['alias'][-1], end="")

#	for wwn in AllWWNList:
#		print ("\n\n", 'WWN: ',wwn, end="")
#		print ("\n", "\t\_zones: ", end="")
#		for zone in DevicesInfo[wwn]['zone']:
#			print (zone, end="; ")
#		print ("\n", "\t\_aliases: ", end="")
#		for alias in DevicesInfo[wwn]['alias']:
#			print (alias, end="")

	print ()



#	print (WWNInfoDict)

#	for zonename, value in fabricConf['effective']['zone'].items():
#		print (zonename, "=> ", end="")
#		for each in value:
#			print (each, end="; ")
#		print ()
#
#	print (json.dumps(fabricConf, ensure_ascii=False))
	
