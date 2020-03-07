#!/usr/bin/env python
# So the general format is python validation.py <<inst_name.xml>>
import xml.etree.ElementTree as ET
import sys
import json
import re
import os
import os.path as path
import random

class inst_validation:
    
    def __init__(self,root):
     
     self.curr_dir_path = os.path.abspath(os.curdir)
     self.parent_dir_path = one_up =  path.abspath(path.join(__file__ ,"../.."))
     self.inst_length = None
     self.output_file = "validation_files/test.txt"
     self.fields = []
	
     # This is the specific instruction file which needs to be translated
     self.inst_file_name = sys.argv[1]
     print "Generating random bitstring for the instruction::" + self.inst_file_name.replace(".xml","")
     self.inst_tree = ET.parse(self.parent_dir_path + "/" + self.inst_file_name)
     self.inst_root = self.inst_tree.getroot()
     self.inst_bitstring = ""
     self.hexstring = ""
     self.hexstring_list = []	       # This stores it in the regular hexadecimal form
     self.hexstring_pickle_list = []   # This one stores the hexstrings in the form which is the input for unicorn

    
    def display_inst_root(self):
         print self.inst_root.attrib

    # generate pickle list with the input version of hexstrings for unicorn
    def generate_pickle_list(self):
	print "Inside generate pickle list"
	stack = []
	for item in self.hexstring_list:
		unicorn_str = ""
		item = item [2:]
		# chop the hexstring
		for i in range(4):
			idx = 2*i
			hex_chop = item[idx:idx+2]
			#print hex_chop
			modified = chr(92) + chr (120) +hex_chop
			# convert to hex string \x<hex>
			#modified =  bytes.fromhex(hex_Chop)
			#print modified			
			stack.append(modified)		
		while len(stack) > 0:
			modified = stack.pop()
			unicorn_str += modified
		unicorn_str = "b" + chr(34) + unicorn_str + chr(34)
		print  unicorn_str
		self.hexstring_pickle_list.append (unicorn_str)
	#print str (self.hexstring_pickle_list)	
    
    def flushall(self):
	self.inst_bitstring = ""
        self.hexstring = ""
	

    # generate an output file that has the randomly generated hex code for unicorn and the printed output file for pvs for an instruction
    def generate_validation_file(self):
        cur_dir = os.path.abspath('')
        self.file_ptr = open(cur_dir +"/" + self.output_file,"w")
	self.flushall()       
	self.generate_binary_inst()
    

    # auto generates a random bitstring and hexstring for the input instruction
    def generate_binary_inst(self):	
	for field in self.fields:
		substr = ""
		f_name = ""
		# 64 bit inst only
		if 'name' in field and field['name'] == "sf":
			substr = "1"
		else:
			if "bitvector" in field and field['bitvector'] != "":
				substr = field ['bitvector']
			elif "width" in field:
				str_len = int(field["width"])
				substr = self.generate_random_bitstring (str_len)
			
		if 'name' in field:
			f_name = field['name']
		else:	
			f_name = "fixed_bitvector"
		print f_name + " = " +  substr
		self.inst_bitstring += substr
	
	self.hexstring = str (hex(int(self.inst_bitstring, 2)))
	print "Bitstring = " + self.inst_bitstring
	print "Hexstring = " + self.hexstring		
				
	
    # view all the regdiagram fields for an instruction
    def view_fields(self):
        for x in self.fields:
            print x

    # fields is a dictionary that keeps track of each field in the xml. the xml tag has the name 'box'. Each field is added to the list self.fields
    def extract_fields(self):
         for node in self.inst_root.findall(".//regdiagram"):
             self.inst_length = node.attrib['form']
             for box in node:
                 field={}
                 bvec=''
                 field.update(box.attrib)
                 for c in box:
                       if c.text is not None:
                           bvec+= c.text
                 field['bitvector']=bvec
                 self.fields.append(field) 

    # generates a random bitsrting of length str_len
    def generate_random_bitstring( self, str_len):
	bitstring = ""
	for i in range (str_len):
		bitstring += str(random.randint(0,1))
        return bitstring
             
if __name__ == '__main__':
	inst_test_suite = inst_validation('')
	inst_test_suite.extract_fields()
	#for i in range(1):				
	inst_test_suite.generate_validation_file()
		#inst_test_suite.view_fields()
	#inst_test_suite.generate_random_bitstring(10)
	inst_test_suite.generate_pickle_list()

