# This code is a util file to extract adhoc information from the xml files such as what inst belong to each class etc.   from the corresponding xml files in ASL. for example generating add_addsub_imm.pvs from add_addsub_imm.xml
# How to run this script? Goto terminal type: python auto_translator_util.py log_imm  and_log_imm.xml. The file and_log_imm.xml or the equivalent file needs to be in the same folder as the script or use the batch_generate.sh script with a filename as an argument taht contains log_imm  and_log_imm.xml
# So the general format is python auto_translator.py <<class_name>> <<inst_name.xml>>
# This file is also used for the autogeneration of the ASL basic fnc and types in the utils.data for a given class by parsing the xml

import xml.etree.ElementTree as ET
import sys
import json
import re
import os
import os.path as path
import pickle

class inst_family:

    def __init__(self,root):
    # This is the master file with all the diagrams for creating the abstract theories
     self.curr_dir_path = os.path.abspath(os.curdir)
     self.parent_dir_path = one_up =  path.abspath(path.join(__file__ ,"../.."))
     self.file_name = "encodingindex.xml"
     self.tree = ET.parse(self.file_name)
     self.root = self.tree.getroot()


     # argv[1[ is always the class name for example addsub_imm or log_imm etc.
     self.cmdline_input = sys.argv[1]
     self.args = re.split("\s+", self.cmdline_input)
     self.extraction_class_name = self.args[0]
     self.extracted_class =""
     self.inst_length = None
     self.file_ptr = None	# file_ptr for translated pvs file
     self.fields =[]
     self.theory_params=[]
     self.theory_params_optional=[]

     # This is the specific instruction file which needs to be translated 
     self.inst_file_name = ""
     # output dir which is used to generate the data files
     self.output_dir = "utils_data/"	
     # if the splitting created more than one argument, this will be used when running this code from the shell script
     if len(self.args) > 1:  
     	self.inst_file_name = self.args[1]
     else:
	self.inst_file_name = sys.argv[2]
     self.inst_tree = ET.parse(self.parent_dir_path + "/" + self.inst_file_name)
     self.inst_root = self.inst_tree.getroot()
     self.theory_name = self.inst_file_name.replace(".xml","")
     self.output_file = self.inst_file_name.replace(".xml",".pvs")
     self.proof_strategy = None
     # Dict for translating the declaration part from ASL to PVS
     self.ASL2PVS_types_map = {"integer": "int", "boolean":"bool", "bits":"bvec", "bit":"bool", "nat":"nat"}	
     # Dict for translating the function names in the declaration part from ASL to PVS => not used till now
     self.ASL2PVS_fncnames_map = {}	
     # A list that hold the names of all xml files for the instructions belongging to a given class. Used in the extract_inst_all_insts_class() method
     self.inst_filenames_for_class = [] 
     # This dictionary holds the name of the fnc used in ASL by an all instructions for a given instruction class.Auto-Extracted from xml files
     self.ASL_fnc_dic_class	= {}	
     # This dictionary holds the name of the types used in ASL by an all instructions for a given instruction class.Auto-Extracted from xml files   	
     self.ASL_types_dic_class  = {}
     # Dic for handling keyword name conflict from ASL to PVS
     self.keyword_name_conflicts = {"type": "type_", "cond" : "cond_"}	
     # A list that holds all the unique pvs signatures and types which are pickled and unpickled 
     self.pvs_fn_signatures = []
     self.pvs_types = []	


    # finds all the instructions for a given class name and stores the filenames for each instruction in a list [000]
    def find_all_insts_class(self):
	# Find the xml element in encoding.xml which has all the instruction information for a given class name => instructiontable
	for node in self.root.findall('.//instructiontable'):
		if node.attrib['iclass'] == self.extraction_class_name:
			# intsructiontable element has many children, we are interested in the tbody element
			for child in node:
				if child.tag == "tbody":
					# loop over every <tr> tag in the <tbody> tag for an instruction class
					for child2 in child:
					        # iformfile attribute holds the name of xml file for an instruction which needs to be added to the elf.inst_filenames_for_class list
						if "iformfile" in child2.attrib:
							# if label attrib exists nly choose the 64 bit else choose
							if "label" in child2.attrib:
								if  child2.attrib['label'] == "64-bit":
									self.inst_filenames_for_class.append(child2.attrib['iformfile'])
                            				else:
                                				self.inst_filenames_for_class.append(child2.attrib['iformfile'])



    # This method extracts the ASL functions and types from the xml for an instruction from the decode part. This method depends on the method find_all_insts_class in order to generate the output as it uses the list returned by this method [001]
    def extract_declarations(self):
         for inst_file in self.inst_filenames_for_class:
		 inst_file_ptr = ET.parse(self.parent_dir_path + "/" + inst_file)
		 #print "Extracting instructions from the file:" + inst_file
		 for node in inst_file_ptr.findall('.//pstext'):
			node.tail
			for child in node:
				if 'hover' in child.attrib:
					# Split the hover attribute to decide if the content is a function or a type
					ASL_element = re.split("\s+", child.attrib['hover'])[0]

					# If the ASL element in hover is a function add to the fnc_dic for the class
					if "function" in ASL_element or "accessor" in ASL_element:
						# add the fnc signature to the class level fnc dictionary
						if child.attrib['hover'] not in self.ASL_fnc_dic_class:
							self.ASL_fnc_dic_class [child.attrib['hover']] = child.attrib['link']
							
					# otherwise add to the types dictionary and will need to change this as per the data and more cases for classification [discussed with Amer]
					else:
						if child.attrib['hover'] not in self.ASL_types_dic_class:
							self.ASL_types_dic_class [child.attrib['hover']] = child.attrib['link']


    # writes the names of ASL fnc and types used in an instruction class into 2 separate files with filename having the class name [002]
    def print_dic_to_file(self):
	f1 = open (self.output_dir + "ASL_fnc_" + self.extraction_class_name , "w")
	#print "Generating the file" + " ASL_fnc_" + self.extraction_class_name
	for key,value in self.ASL_fnc_dic_class.items():
		f1.write(key + "\n")
	f2 = open (self.output_dir + "ASL_types_" + self.extraction_class_name , "w")
	#print "Generating the file" + " ASL_types_" + self.extraction_class_name
	for key,value in self.ASL_types_dic_class.items():
		f2.write(key + "\n")

    # generates the output file that has all the pvs signatures	
    def generate_pvs_fn_file(self):
	#print self.pvs_fn_signatures
	output_filename = self.output_dir + "ASL_fnc.pvs"
	if os.path.exists(output_filename):
    		append_write = 'a' # append if already exists
	else:
    		append_write = 'w'	
	output_fn_file = open (output_filename ,append_write)
	for signature in self.pvs_fn_signatures:
		output_fn_file.write (signature + "\n")
    
    # generates the output file that has all the pvs signatures	
    def generate_pvs_types_file(self):
	output_filename = self.output_dir + "ASL_types.pvs"
	if os.path.exists(output_filename):
    		append_write = 'a' # append if already exists
	else:
    		append_write = 'w'	
	output_types_file = open ( output_filename ,append_write)
	for pvs_type in self.pvs_types:
		output_types_file.write (pvs_type)	



    # Extract the xml element which holds all the information for a given classname from encoding.xml to simplify processing
    def extract_inst_class(self):
        for node in self.root.findall('.//iclass_sect'):
            #print node.attrib
            if node.attrib['id'] == self.extraction_class_name:
                self.extracted_class = node
  
    # method to auto-generate the file ASL_types.pvs [003]
    def convert_ASL_types_to_PVS (self):
	# Assumption intermediate file with the name ASL_<classmname> exists in the utils_data dir which has all ASL types for a particular class
	f = open (self.output_dir + "ASL_types_" + self.extraction_class_name ,"r")	
	for line in f: 
		line = line.strip()
		ASL_type_tokens = re.split("\s+", line)
		pvs_type = self.ASL_types_to_PVS(ASL_type_tokens, line)
		if pvs_type not in self.pvs_types:
			self.pvs_types.append(pvs_type)
			


 
    # helper method that takes a list of ASL_type_tokens as an input, and converts the ASL tokens into PVS [003/4h]	
    def ASL_types_to_PVS (self, ASL_type_tokens, line):
		if ASL_type_tokens[0] == 'enumeration':
			ASL_type = ASL_type_tokens [0]
			ASL_type_name = ASL_type_tokens [1]
			# variable that holds the converted type in PVS 
			ASL_type_arg = ""
			arg_cntr = 0
			for i in range (2, len(ASL_type_tokens)):	# re.split breaks the arguments into single strings because of space, we need to put them together again			
				
			        if len(ASL_type_tokens) >= 10:
					ASL_type_arg = ASL_type_arg + ASL_type_tokens[i] + "\n"	
				else: 	
					ASL_type_arg = ASL_type_arg + ASL_type_tokens[i]																																											
			return (ASL_type_name + ":" +  " Type+ = " +  ASL_type_arg + "\n")
		elif ASL_type_tokens[0] in self.ASL2PVS_types_map:
			self.ASL2PVS_types_map[ASL_type_tokens[0]]
			return ASL_type_arg
		else:
			return ("% not implemented::" + str(ASL_type_tokens) + "\n")

    # Converts an ASL argument in a fn signature and to PVS equivalent.
    def ASL_types_to_PVS_fn (self, ASL_arg):
	ASL_arg_tokens = re.split("\s+", ASL_arg)
	PVS_type = ""
	ASL_arg_type = ""
	arg_name = ""
	ASL_arg_tokens_nospaces = []
	# remove tokens that are empty or with spaces
	for token in ASL_arg_tokens:
		if  not token  or token.isspace():
			continue
		else:
			ASL_arg_tokens_nospaces.append(token)
	
	ASL_type = ASL_arg_tokens_nospaces [0]
	# for extracting "y" => "bit(N) y"
	if len (ASL_arg_tokens_nospaces) > 1:
		arg_name = ASL_arg_tokens_nospaces [1]
		# resolve PVS name conflicts
		if arg_name in self.keyword_name_conflicts:
			arg_name = self.keyword_name_conflicts[arg_name]
		
	# extract the type and the arg in between the (). for e.g. bits (N)
	if "(" in ASL_type:
		ASL_type_res = ASL_type.split ("(")[1]
		ASL_type = ASL_type.split ("(")[0]				
		PVS_type = self.ASL2PVS_types_map [ASL_type] + " (" + ASL_type_res
		# replace "()" by "[]" if PVS_type = "bvec"
		if self.ASL2PVS_types_map [ASL_type] == "bvec":
			PVS_type = PVS_type.replace("(","[")
			PVS_type = PVS_type.replace(")","]")
	else:
		if ASL_type in self.ASL2PVS_types_map:
			PVS_type = 	self.ASL2PVS_types_map [ASL_type]
		else: 
			PVS_type = ASL_type
	if not arg_name:	 
		return PVS_type
	else: 
		return arg_name + " : " + PVS_type

    # Extract fn name from a string using regex
    def extract_ASL_fn_name(self,str):
	return re.findall(r'[A-Z]+[a-z,A-Z,\d]*\(',str)

    # A helper function to return the string beyween a well formed parenthesis
    def extract_arg_list(self, str):
	count = 0
	start_idx = 0
	end_idx = 0
	idx = 0
	flag = -1
	arg_list = []
	for i in str:		
		if i == "(":
		    count += 1
		    flag = 0
		    if count == 1:
			start_idx = idx
		elif i == ")":
		    count -= 1
		if count == 0 and flag == 0:
		    flag = -1
		    end_idx = idx
		    arg_list.append( str[start_idx+1:end_idx])
		idx+=1
	return arg_list
    
    # helper method to separate arguments and return a list of indivdual arguments
    def separate_args(self, arg_tuple):
	arg_list = re.split(",",arg_tuple)
	return arg_list

    # method to auto-generate the file ASL_fnc.pvs [004]
    def convert_ASL_fn_to_PVS (self):
	input_file = open (self.output_dir + "ASL_fnc_" + self.extraction_class_name ,"r")
	for line in input_file:				
		line = line.strip()
	        print "Input ASL signature:\t" + line
		arg_list = []
		pvs_signature = ""
		tokens = re.split("\s+", line)
		ASL_fnc_signature = line.split(None,1)[1]
		# token 0 can either be a string "function:" or "accesor:"		
		if "function" in tokens[0]:			
			pattern5 = re.compile("[A-Z][a-z,A-Z,\d]*\(.*\)")
			pattern_UCase = re.compile("[A-Z]")
			# function signatures have a return type with one or more than one argument
			if len(tokens) > 2:
				
				ASL_fnc_name = self.extract_ASL_fn_name (ASL_fnc_signature)
				arg_tuples_list = []
								
				# For e.g. tokens = (bits(N), bits(4)) AddWithCarry(bits(N) x, bits(N) y, bit carry_in)
				if tokens[1].startswith("("):					
					arg_tuples_list = self.extract_arg_list (str(ASL_fnc_signature))
					pvs_signature = self.create_PVS_sign_case_1 (ASL_fnc_name, arg_tuples_list)
					
				# For e.g. tokens = "bits(N)" "NOT(bits(N) x)"				
				elif not tokens[1].startswith("(") and "(" in tokens[1] and re.match (pattern_UCase, tokens[1][0]) is None:
					pvs_signature = self.create_PVS_sign_case_2 (ASL_fnc_name, ASL_fnc_signature) 

				#Prefetch(bits(64) address, bits(5) prfop)
			        elif re.match(pattern5, ASL_fnc_signature ) is not None:					
					arg_tuples_list = self.extract_arg_list (str(ASL_fnc_signature))
					pvs_signature = self.create_PVS_sign_case_1 (ASL_fnc_name, arg_tuples_list)

				# For e.g. tokens = integer UInt(bits(N) x)
				else:
					pvs_signature = self.create_PVS_sign_case_3 (ASL_fnc_name, ASL_fnc_signature)	
				
			# function return type does not have a return type or parameters
			else:
				pvs_signature = self.create_PVS_sign_case_4(tokens)
			
		else:
			pvs_signature = "% not implemented::" + line + "\n"
		# append the signature to the list of fn signatures
		if pvs_signature not in self.pvs_fn_signatures:
			self.pvs_fn_signatures.append(pvs_signature)
		print "Output PVS signature:\t" + pvs_signature + "\n"
		if ASL_fnc_signature not in self.ASL2PVS_fncnames_map:
			self.ASL2PVS_fncnames_map [ASL_fnc_signature] = pvs_signature

    

    
    # helper method to create the PVS fn signature from ASL fn which has multiple return arguments. arg_list: list of arg tuples 'bits(N), bits(4)'
    def create_PVS_sign_case_1 (self, ASL_fnc_name, arg_tuples_list):
	#print arg_tuples_list
	PVS_arg_str_list = []	
	ASL_fnc_name = ASL_fnc_name[0][:-1]
	tuple_cnt = 0	
	# arg_list can multiple args such as bits(N), bits(4)				
	for arg_tuple in arg_tuples_list:
		PVS_arg = ""
		PVS_arg_str = ""		
		# "bits(N), bits(4)" => ["bits(N)", "bits(4)"]
		arg_list = self.separate_args (arg_tuple)
		for arg in arg_list:
			# convert the ASL arg to its PVS equivalent
			PVS_arg = self.ASL_types_to_PVS_fn (arg)
			# handle commas
			if PVS_arg_str == "":
				PVS_arg_str = PVS_arg_str + PVS_arg
			else:
				PVS_arg_str = PVS_arg_str + " , " +  PVS_arg
		tuple_cnt+=1
		# change enclosing parenthesis depending on if its the fn parameter list or the return type list
		if tuple_cnt == 1 and len (arg_tuples_list) > 1 :
			PVS_arg_str = "[" + PVS_arg_str + "]"
		else:
			PVS_arg_str = "(" + PVS_arg_str + ")"
		# append to list
		PVS_arg_str_list.append (PVS_arg_str)
	if len (arg_tuples_list) > 1:
		return ASL_fnc_name + " " + str (PVS_arg_str_list[1]) + " : " + str (PVS_arg_str_list [0]) + "\n"
	else:
		return ASL_fnc_name + " " + str (PVS_arg_str_list[0])  + " : []" + "\n"	


    # helper method to create the PVS signature for an ASL function with one argument that has no parenthesis and adds it to the gloabl dic
    def create_PVS_sign_case_2 (self, ASL_fnc_name, ASL_fnc_signature):
	arg_tuples_list = []
	return_type = ASL_fnc_signature.split(None, 1)[0]
	arg_tuples_list.insert(0, return_type)
	# temp_list gets the parameters
	temp_list = self.extract_arg_list (str(ASL_fnc_signature))
	# add temp_list to arg_tuples list omitting temp_list[0]
	for i in range (1,len(temp_list)):
		arg_tuples_list.append(temp_list[i])							
	pvs_signature = self.create_PVS_sign_case_1 (ASL_fnc_name, arg_tuples_list)
	return pvs_signature	
	
    # helper method that creates the PVS signature for an ASL function with one argument  and adds it to the gloabl dic
    def create_PVS_sign_case_3 (self, ASL_fnc_name, ASL_fnc_signature):
	arg_tuples_list = []
	return_type = ASL_fnc_signature.split(None, 1)[0]
	arg_tuples_list.insert(0, return_type)
	# temp_list gets the parameters
	temp_list = self.extract_arg_list (str(ASL_fnc_signature))
	# add temp_list to arg_tuples list omitting temp_list[0]
	for i in temp_list:
		arg_tuples_list.append(i)								
	pvs_signature = self.create_PVS_sign_case_1 (ASL_fnc_name, arg_tuples_list)
	return pvs_signature

    # helper method that creates the PVS signature for an ASL function with no arguments and adds it to global dic 
    def create_PVS_sign_case_4 (self,tokens):	
	ASL_fnc_name = tokens[1]
	ASL_fnc_return_type = ""
	# Add the corresponding fnc name from the fnc names map. Identity fnc							
	if ASL_fnc_name not in self.ASL2PVS_fncnames_map:
		self.ASL2PVS_fncnames_map [ASL_fnc_name] = ASL_fnc_name
	return ASL_fnc_name + "\n"
	#print ASL_fnc_name + "\t case IV"

    # Pickle the converted PVS fn
    def pickle_pvs_fn(self):
	filename = self.output_dir + "pickled_pvs_fn"
	outfile = open(filename,'wb')
	pickle.dump (self.pvs_fn_signatures, outfile)
	outfile.close()
	
    # Pickle the converted PVS types
    def pickle_pvs_types(self):
	filename = self.output_dir + "pickled_pvs_types"
	outfile = open(filename,'wb')
	pickle.dump (self.pvs_types, outfile)
	outfile.close()

    # Load the pickled fn and types into the lists
    def unpickle_lists(self):
	filename_fn = self.output_dir + "pickled_pvs_fn"
	infile_fn = open(filename_fn,'rb')
	self.pvs_fn_signatures = pickle.load(infile_fn)
	infile_fn.close()

	filename_types = self.output_dir + "pickled_pvs_types"
	infile_types = open(filename_types,'rb')
	self.pvs_types = pickle.load(infile_types)
	infile_types.close()


inst_imm = inst_family('')
# finds all instructions for an ARM class
inst_imm.find_all_insts_class()
# 
inst_imm.extract_declarations()
# generates the intermediate files for ASL fn and ASL types for a class
inst_imm.print_dic_to_file()
# initialize the self.pvs_fn_signatures and self.pvs_types list with the older data
inst_imm.unpickle_lists()
# converts the ASL fn and types to corresponding PVS
inst_imm.convert_ASL_types_to_PVS()
inst_imm.convert_ASL_fn_to_PVS ()
# prints the pvs signatures to the output file 
#inst_imm.generate_pvs_fn_file()
#inst_imm.generate_pvs_types_file()
inst_imm.pickle_pvs_fn()
inst_imm.pickle_pvs_types()





