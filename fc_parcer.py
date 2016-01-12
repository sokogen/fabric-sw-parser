#!/usr/bin/python3
# Parcer FiberZone files
# Author: Sokogen
import json,sys

def GetDeviceAddresses(filename):
	"Getting of addresses for all devices."
	for line in open(zoneFileName, 'r'):
			if line.split('\t')[0].strip() == "zone:":
				continue
			elif line.strip() in DeviceAddressList:
				continue
			else:
				DeviceAddressList.append(line.strip())
	return DeviceAddressList

def FindZones(deviceAddr):
	"Associating each device address used with all its zones."
	for line in open(zoneFileName, 'r'):
		if line.split('\t')[0].strip() == "zone:":
			zone = line.split('\t')[1].strip()
		else:
			if line.strip() == deviceAddr:
				zoneList.append(zone)
	return zoneList

if __name__ == "__main__":
	if len(sys.argv) == 1:
		print ("Add filename.", "\n" ,"\'parcer.py file_name\'")
		exit()
	elif len(sys.argv) > 2:
		print ("Too many arguments.", "\n" ,"\'parcer.py file_name\'")
		exit()
	else:
		dict={}
		zoneFileName=sys.argv[1]
		DeviceAddressList=[]
		
		GetDeviceAddresses(zoneFileName)
	
		for device in DeviceAddressList:
			zoneList=[]
			FindZones(device.strip())
			dict[device.strip()] = zoneList
		for key, value in sorted(dict.items()):
			print (key, ';' ,", ".join(value))
		
		#print (json.dumps(dict, ensure_ascii=False))
	
