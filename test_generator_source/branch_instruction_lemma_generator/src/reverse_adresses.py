from bitstring import BitArray, BitStream, BitString
import json
from pprint import pprint
import re
import os
from ctypes import *

def pvs_address_extractor():
	addressHash = {}
	inputFile = "../assets/pvs_files/CURRENT_TIME_FFFFFFFF0001C100.pvs"
	filePtr = open(inputFile, "r")
	count = 1
	instruction = ""
	lastLineTokens = []
	firsLineTokens = []
	for ln in filePtr:
		tokens = ln.split()
		idx = -1
		for part in tokens:
			if "addr:=" in part:
				idx = tokens.index(part)
				break
		if idx != -1:
			currAddr = extract_string_between_characters(tokens[idx + 1], '(', ')')
			addressHash[count] = bin(int(currAddr))
			count += 1

	return addressHash

def json_offset_value_extractor():
	offsetHash = {}
	inputFile = "../assets/json_files/current_time.json"

	with open(inputFile) as dataFile:
		inputHash = json.loads(dataFile.read())
	blockList = inputHash[0]['blocks'][0]['ops']
	count = 1
	for block in blockList:
		offsetHash[count] = bin(c_ulong(block['offset']).value)
		count += 1

	return offsetHash

def extract_string_between_characters(str, nameStart, nameEnd):
	substr = (str.split(nameStart))[1].split(nameEnd)[0]	
	return substr

def compare_two_hashes(hashA, hashB):
	for k, v in hashA.items():
		if hashA[k] != hashB[k]:
			return False
	return True

def verify_address_translation():
	pvsAddr = pvs_address_extractor()
	radareAddr = json_offset_value_extractor()
	print("PVS = ", pvsAddr)
	print("Radare = ", radareAddr)

	flag = compare_two_hashes(pvsAddr, radareAddr)
	print("EQUAL = ", flag)

verify_address_translation()
