from bitstring import BitArray, BitStream, BitString
import json
from pprint import pprint
import re
import os
from ctypes import *
import subprocess

def address_parser(pvsFileName):
	responseDict = {}
	file_ptr = open(pvsFileName, "r")
	count = 0
	instruction = ""
	last_line_tokens = []
	first_line_tokens = []
	for ln in file_ptr:
		if count == 0:
			first_line_tokens = ln.split("_")
			print("fist line tokens", first_line_tokens)
		last_line_tokens = ln.split("_")
		tokens = ln.split()
		for part in tokens:
			if "addr:=" in part:
				idx = tokens.index(part)
		count += 1

	hex_string = ""
	for token in last_line_tokens:
		hex_string = token.strip()

	first_line_tokens_last_index = len(first_line_tokens) - 2
	instrctuon_tokens = first_line_tokens[:first_line_tokens_last_index]
	for token in instrctuon_tokens:
		instruction += token + "_"
	last_char_instruction = len(instruction)
	final_instruction = instruction[:last_char_instruction - 1]

	h_bit_stream = BitString("0x" + hex_string)
	offset = h_bit_stream.int
	uint_offset = UInt(hex_string)
	responseDict['hexString'] = hex_string
	responseDict['offset'] = offset
	responseDict['offsetUint'] = uint_offset
	responseDict['instruction'] = final_instruction

	print("responseHash = ", responseDict)
	return responseDict

def UInt(string):
	h_bit_stream = BitString("0x" + string)
	uint_offset = h_bit_stream.uint
	return uint_offset

def extract_jump_and_fail_values(addressDict):
	jumpFailObj = {}
	offset = addressDict['offset']
	#pass the JSON name here for automation
	jsonFileName = get_json_name_for_pvs_file(addressDict['instruction'].lower())
	input_file = "../assets/zircon/json_files/sym." + jsonFileName + ".json"
	with open(input_file) as data_file:
		input_hash = json.loads(data_file.read())
	block_list = input_hash[0]['blocks']

	# ret instruciton does not have a jump or fail value for it
	for block in block_list:
		if block["offset"] == offset:
			if 'fail' in block and 'jump' in block:
				jumpFailObj['fail'] = subprocess.check_output(["rax2", str(block['fail'])])[:-1]
				jumpFailObj['jump'] = subprocess.check_output(["rax2", str(block['jump'])])[:-1]
			elif 'fail' in block and 'jump' not in block:
				jumpFailObj['fail'] = subprocess.check_output(["rax2", str(block['fail'])])[:-1]
			elif 'fail' not in block and 'jump' in block:
				jumpFailObj['jump'] = subprocess.check_output(["rax2", str(block['jump'])])[:-1]
			break
		else:
			continue

	return jumpFailObj

def extract_branch_instruction_line(pvsFileName):
	branchInstructionList = ['b_cond']
	inputFile = open(pvsFileName, 'r')
	reqLine = ""
	responseDict = {}
	instName = ""
	pvsFncName = pvsFileName.rsplit('_', 1)[0].lower()

	for inst in branchInstructionList:
		for line in inputFile:
			lineTrimmed = line.strip()
			lineFormatted = " ".join(lineTrimmed.split())
			if len(lineFormatted) > 0 and lineFormatted.startswith(inst):
				instName = extract_string_between_characters(lineFormatted, '= ', ' [')
				if instName == inst:
					reqLine = str(line)
					break
			else:
				continue
	if len(reqLine) > 0:
		lineToBeExtracted = replace_string_between_characters(reqLine, ' p ', '[', ']')
		responseDict['instName'] = instName
		responseDict['line'] = lineToBeExtracted

	return responseDict

def replace_string_between_characters(string, ch, start, end):
	firstDelPos = string.find(start) # get the position of [
	secondDelPos = string.find(end) # get the position of ]
	stringAfterReplace = string.replace(string[firstDelPos + 1 : secondDelPos], ch)
	return stringAfterReplace

def extract_string_between_characters(line, nameStart, nameEnd):
	instName = (line.split(nameStart))[1].split(nameEnd)[0]
	return instName

def extract_pre_address(instDict):
	line = instDict['line']
	lineTrimmed = line.strip()
	lineFormatted = " ".join(lineTrimmed.split())
	temp = extract_string_between_characters(lineFormatted, 'addr:= ', '}}')
	preAddr = subprocess.check_output(["rax2", temp])[:-1]

	return preAddr

def test_lemma_generator():
	dirPath = '../assets/zircon/pvs_files/'
	batchFile = 'p.batch_dec'
	batchPtr = open (dirPath + batchFile, "r")

	for pvsFileName in batchPtr:
		input_file = pvsFileName.strip().upper() + ".pvs"
		pvsFilePath = '../assets/zircon/pvs_files/' + input_file
		instDict = extract_branch_instruction_line(pvsFilePath)
		print("instDict = ", instDict)
		if bool(instDict): 
			print("\n\n\n")
			addressDict = address_parser(pvsFilePath)
			print("\n\n\n")
			print("addre dict = ", addressDict)
			print("\n\n\n")

			jumpFailDict = extract_jump_and_fail_values(addressDict)
			print("JUMP Fail obj =", jumpFailDict)

			preAddr = extract_pre_address(instDict)
			print("\n\n", preAddr)

			pvsLemmaFilename = instDict['instName'] + '_' + addressDict['hexString']
			print("\n\n", pvsLemmaFilename)
			curDir = os.path.abspath('')
			outputDir = curDir + "/zircon_test_lemmas/"
			f = open(outputDir + pvsLemmaFilename + ".pvs", "w")

			instLine = instDict['line']
			lineTrimmed = instLine.strip()
			lineFormatted = " ".join(instLine.split())
			
			jump = ""
			fail = ""

			if 'jump' and 'fail' in jumpFailDict:
				jump = str(jumpFailDict['jump'])
				fail = str(jumpFailDict['fail'])
			elif 'jump' in jumpFailDict and 'fail' not in jumpFailDict:
				jump = str(jumpFailDict['jump'])
			elif 'jump' not in jumpFailDict and 'fail' in jumpFailDict:
				fail = str(jumpFailDict['fail'])
				

			f.write(pvsLemmaFilename)
			f.write("      : THEORY")
			f.write("\n    BEGIN")
			f.write("\n    IMPORTING rsl@" + instDict['instName'])
			f.write("\n        X_sts : [ below(32) -> bvec[64] ]  = init`X ]\n")
			f.write("\n        p    :  s = init with [`X:= X_sts]  with [ `PC := " + str(preAddr) + " ]\n")
			f.write("\n    " + lineFormatted)

			if len(jump) > 0 and len(fail) > 0: 
				f.write("\n    test1 : lemma let X_post =  p`PC = " + str(jumpFailDict['fail']) + " or " + str(jumpFailDict['jump']) + "\n\n")
			elif len(jump) > 0 and len(fail) <= 0:
				f.write("\n    test1 : lemma let X_post =  p`PC = " + str(jumpFailDict['jump']) + "\n\n")
			elif len(jump) <= 0 and len(fail) > 0:
				f.write("\n    test1 : lemma let X_post =  p`PC = " + str(jumpFailDict['fail']) + "\n\n")

			f.write("\n\n%|- X_sts_TCC*      : PROOF")
			f.write("\n%|- conc_test_1_TCC*: PROOF")
			f.write("\n%|- test1_TCC1      : PROOF (eval-formula)")
			f.write("\n%|- QED")
			f.write("%|- test1 : PROOF ( b_cond ))")
			f.write("\n%|- QED")
			f.write("\nEND " + pvsLemmaFilename)
		else:
			continue


def test_lemma_generator_with_bitvector():
	dirPath = '../assets/zircon/pvs_files/'
	batchFile = 'p.batch_dec'
	batchPtr = open (dirPath + batchFile, "r")

	for pvsFileName in batchPtr:
		input_file = pvsFileName.strip().upper() + ".pvs"
		pvsFilePath = '../assets/zircon/pvs_files/' + input_file
		instDict = extract_branch_instruction_line(pvsFilePath)
		print("instDict = ", instDict)
		if bool(instDict): 
			print("\n\n\n")
			addressDict = address_parser(pvsFilePath)
			print("\n\n\n")
			print("addre dict = ", addressDict)
			print("\n\n\n")

			jumpFailDict = extract_jump_and_fail_values(addressDict)
			print("JUMP Fail obj =", jumpFailDict)

			preAddr = extract_pre_address(instDict)
			print("\n\n", preAddr)

			pvsLemmaFilename = instDict['instName'] + '_' + addressDict['hexString'] + '_bitvector'
			print("\n\n", pvsLemmaFilename)
			curDir = os.path.abspath('')
			outputDir = curDir + "/zircon_test_lemmas/"
			f = open(outputDir + pvsLemmaFilename + ".pvs", "w")

			instLine = instDict['line']
			lineTrimmed = instLine.strip()
			lineFormatted = " ".join(instLine.split())
			
			jump = ""
			fail = ""

			if 'jump' and 'fail' in jumpFailDict:
				jump = str(jumpFailDict['jump'])
				fail = str(jumpFailDict['fail'])
			elif 'jump' in jumpFailDict and 'fail' not in jumpFailDict:
				jump = str(jumpFailDict['jump'])
			elif 'jump' not in jumpFailDict and 'fail' in jumpFailDict:
				fail = str(jumpFailDict['fail'])

			addressExtracted = extract_string_between_characters(lineFormatted, 'addr:= ', '}}').strip()
			print("ADDRESS = ", addressExtracted)
			binAddressExtracted = str(bin(int(addressExtracted))).zfill(64)[2:][::-1]
			secondPart = 'next:= ' + jumpFailDict['jump'] + ', fail:= ' + jumpFailDict['fail'] + ' }}'

			#delete the string between two strings
			holder = re.sub('addr:=.*?}}','',lineFormatted, flags = re.DOTALL)
			firstPart = replace_string_between_characters(holder, '{Diag:= bv[32] ', '{{Diag:=', '(')
			newLine = firstPart + secondPart
			instructionName = newLine.split(':')[0].strip()

			f.write(pvsLemmaFilename)
			f.write("      : THEORY")
			f.write("\n    BEGIN")
			f.write("\n    IMPORTING rsl@arm_state, rsl@" + instDict['instName'])
			f.write("\n\n        X_sts : [ below(32) -> bvec[64] ]  = init`X \n")
			# f.write("\n        p    :  s = init with [`X:= X_sts]  with [ `PC`b := bv[64] (0b" + str(bin(int(str(preAddr)))).zfill(64)[2:][::-1] + ") ]\n")
			f.write("\n        p    :  s = init with [`X:= X_sts]  with [ `PC`b := " + preAddr + " ]\n")
			f.write("\n    " + newLine)

			if len(jump) > 0 and len(fail) > 0:
				print(" jump + fail")
				f.write("\n\n    test1 : lemma " + instructionName + ".post`PC`b = " + jumpFailDict['jump'] + " or ")
				f.write("\n                  " + instructionName + ".post`PC`b = " + jumpFailDict['fail'] + "\n\n")
			elif len(jump) > 0 and len(fail) <= 0:
				print(" jump")
				f.write("\n\n    test1 : lemma " + instructionName + ".post`PC`b = " + jumpFailDict['jump'])
				# f.write("\n\n    test1 : lemma " + instructionName + ".post`PC`b = bv[64](0b" + str(bin(jumpFailDict['jump'])).zfill(64)[2:][::-1] + ")\n\n")
			elif len(jump) <= 0 and len(fail) > 0:
				print("fail")
				f.write("\n\n    test1 : lemma " + instructionName + ".post`PC`b = " + jumpFailDict['fail'])
			
			f.write('\n    test2: lemma ConditionHolds[p](' + instructionName + '.condition) => ' + instructionName + '.post`PC`b = ' + jumpFailDict['jump'])
			f.write('\n\n    test3: lemma NOT ConditionHolds[p](' + instructionName + '.condition) => ' + instructionName + '.post`PC`b = ' + jumpFailDict['fail'])
			
			f.write("\n\n%|- p_TCC1         : PROOF")
			f.write("\n%|- " + instructionName + "_TCC*: PROOF")
			f.write("\n%|- test1_TCC1      : PROOF (eval-formula)")
			f.write("\n%|- QED")

			f.write("\n\n%|- test1_TCC2 :PROOF")
			f.write("\n%|- test3_TCC1 :PROOF (eval-formula 2) QED")
	
			f.write("\n\n%|- test* : PROOF ( b_cond )")
			f.write("\n%|- QED")

			f.write("\n\nEND " + pvsLemmaFilename)
		else:
			continue

def get_json_name_for_pvs_file(pvsFncName):
	f = open('../zircon_terminals_modified_names.json', 'r')
	modifiedFuncNamesHash = json.load(f)
	lowerCaseDict = {}
	# since the cases keys are case-sensitive we are creating a new dict with new {key, val} pairs
	for k,v in modifiedFuncNamesHash.items():
		lowerCaseDict[k.lower()] = v

	return lowerCaseDict[pvsFncName]

# test_lemma_generator()
test_lemma_generator_with_bitvector()
