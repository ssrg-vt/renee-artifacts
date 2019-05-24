# This script is used for validation of auto-decoder output. The starting point is a batch file with the file names of pvs files to be validated. It compares the instructions in the output pvs files and matches their bytecode with their name. It is a rveerse lookup

import xml.etree.ElementTree as ET
import sys
import json
import re
import collections
import time
import os


class inverse_dict:
    def __init__(self):
        print ("Parsing output pvs file...\n")
        self.current_path = os.getcwd().strip() +"/"
        self.ASL_files_dir = "/assets/ASL_xml_files/"   
        self.inputfiles_dir = "/output_pvs_files/"
        # This directory is used to extract the bytecode from the .dec file for a corresponding .pvs output file
        self.bytecode_validation_dir = "/assets/intermediate_dec_files/"
        self.output_dir = self.current_path + "/assets/output_stats_files/"

        # Supporting input file section
        self.file_name = "encodingindex.xml"
        path = self.current_path + self.ASL_files_dir
        #os.listdir(path)
        encoding_file_path = os.path.join(path, self.file_name)
        file_ptr = open(encoding_file_path,"r")
        #print ("Opening file: " + fullname)
        self.tree = ET.parse(encoding_file_path)
        self.root = self.tree.getroot()
        # List to store the names of instructions from the output .pvs file
        self.inst_names_list = []
        # List to store the bytecodes extracted from .dec files for cprresponding .pvs file
        self.inst_bytecodes =[]
        # List to store all the extracted bitstrings
        self.inst_bitstrings = []
        
        # List holds the fields for the entire class
        self.inst_class_fields = []

        # A dictionary that holds the elements from the self.inst_fields as the key ("sp") and the bit value for an instruction as the value
        self.inst_field_values = {}
        # Additional file pointers incase the instruction file needs to be parsed directly instead of
        self.inst_filename = None
        self.inst_fileptr = None


        # This keeps track of the current instruction name
        self.current_inst_name = None
        self.current_inst_class = None
        self.current_bitstring = None
        self.current_bytecode = None
     
        # This is dummy data for testing
        #self.current_inst_name = "add_addsub_shift"
        #self.current_inst_class = "addsub_shift"
        #self.current_bitstring = "01000100000000000100000011010001"
        #self.current_bytecode = ""
    
    # Helper method to extract class fields from the xml of the instrcution directly such as movk.xmk. Used for instructions that do not have class name such as movz, adrp
    def extract_xml_node_from_inst_xml(self, inst, node_name):
        self.inst_filename = inst + ".xml"
        path = self.current_path + self.ASL_files_dir
        os.listdir(path)
        fullname = os.path.join(path, self.inst_filename)
        inst_file_ptr = open(fullname,"r")
        #print ("Opening file: " + fullname)
        inst_tree = ET.parse(fullname)     
        inst_root = inst_tree.getroot()
        #for anode in inst_root:
         #   print anode.tag
        for node in inst_root.find("classes"):
                    #print node.tag
                    if node.tag=="iclass":
                         for cnode in node:
                            #print cnode.tag
                            # extract the regdiagram info 
                            if cnode.tag == "regdiagram":
                                return cnode
                            # Extract fields and values from the encoding section for each instruction such as sf==1 for 64 bit instruction such as movz
     
    # Loops through all the instructions in the list of extracted instructions and extracts their pattern
    def validate_instructions(self):
        counter = 0
        for inst in self.inst_names_list:
            #print ("Counter =" + str(counter))
            self.current_bitstring = self.inst_bitstrings[counter]
            self.current_inst_name = inst
            print ("\n\nCurrent instruction name is:" + self.current_inst_name)
            print ("Current bitstring is:" + self.current_bitstring)

            # Extract the instruction class from the instruction name by splitting on first occurence of "_"
            if len(inst.split("_",1)) > 1 and "ldr" not in inst and "str" not in inst:
                self.current_inst_class = inst.split("_",1)[1]
                #print ("Current instruction class is:" + self.current_inst_class)
                self.extract_inst_pattern()
            else:  
                #print ("Special class\n") 
                # This fetches the regdiagram xml node from the inst.xml file directly such as movk.xml             
                regdiagram_node = self.extract_xml_node_from_inst_xml (inst, "regdiagram")
                # This extracts the actual fields from the regdiagram
                self.extract_class_fields_from_regdiagram(regdiagram_node)              
            #Extract the corresponding bytecode
            self.current_bytecode = self.inst_bytecodes[counter] 
            print ("Comparing bytecode pattern for inst:" + self.current_inst_name)
            self.print_dict()
            self.match_bytecode_pattern()
            self.convert_bitstring_to_bytecode()
            counter+=1
    
    # Parse a .dec file and extract the bytecodes from it for validation
    def parse_dec_file(self, filename):
        fileptr = open(self.current_path + self.bytecode_validation_dir + filename,"r")
        # for every line in output pvs file for blocks
        #print "Extracting bytecode from " + filename
        print "\nExtracting bytecodes form radare2 json file for corresponding the output pvs file"
        for line in fileptr:
            # Filter out other lines and keep only lines with inst names         
            tokens = re.split("\s+",line)
            # instruction name extracted from the tokens array   
            print(tokens[1])
            self.inst_bytecodes.append(tokens[1])
        
        
    # This functions takes the output pvs filename as an argument and parses it to extract the instruction names such as add_addsub_imm
    def parse_pvs_file(self,filename):
        fileptr = open(self.current_path + self.inputfiles_dir + filename,"r")
        print "Extracting inst names from " + filename
        # for every line in output pvs file for blocks
        for line in fileptr:
            # Filter out other lines and keep only lines with inst names
            if "Theory" in line:
                tokens = re.split("\s+",line)
                # instruction name extracted from the tokens array
                print(tokens[5])
                self.inst_names_list.append(tokens[5])
                self.inst_bitstrings.append(tokens[11][2:])
    
    # This function extracts the abstract pattern of an instruction from its name which will be used in the validation of the output pvs file. A flag is used to distinguish between instructions for which class is extracted or not. 
    def extract_inst_pattern(self):      
        #print ("Extracting the pattern for instruction ::" + self.current_inst_name)
        # If instrcution class has been extracted from the instruction name such as addsub_ imm from add_addsub_imm      
        for node in self.root.findall('iclass_sect'):
            if node.attrib['id'] == self.current_inst_class:
                #print("Extracted class is:\t" + str(node.attrib))              
                for child in node:
                    # extract the corresponding regdiagram for the instruction class
                    if child.tag == "regdiagram":                        
                        self.extract_class_fields_from_regdiagram(child)
                    # extract the corresponding instruction soecific bits such as sf, op from the instructiontable tag
                    if child.tag == "instructiontable":
                        self.extract_inst_fields(child)
        # For instructions such as movz, adrp where class cannot be extracted from the name of inst

    # Helper method to extract the diagram pattern and store in the self.inst_class_fields dict                  
    def extract_class_fields_from_regdiagram(self, child):
        for box in child:
            fixed_pattern = ""
            #print box.attrib                          
            for c_tag in box:
                if c_tag.text is not None:
                    fixed_pattern += c_tag.text
            if fixed_pattern is not "":
                #print fixed_pattern
                box.attrib["fixed_pattern"] = fixed_pattern
            # append all the fields to the dict
            self.inst_class_fields.append(box.attrib)

    # Helper method to extract the field names and values whoch are specific for a particular instruction within a class such as sf==1
    def extract_inst_fields(self,child):
        inst_fields = []
        inst_field_values = []
        for xml_elem in child:
            # search in the thead tag
            if xml_elem.tag == "thead":
                for tr in xml_elem:
                    # search in the tr tag with attrib heading2
                    if tr.attrib['id'] == "heading2":                                       
                        # Find the fields in the class which are variable such as sf, op etc. and put them in a list
                        for th in tr:
                            inst_fields.append(th.text) 
            # goto the tbody elem
            if xml_elem.tag == "tbody": 
                # list for holding the bit values                             
                for tr in xml_elem:
                    file_name = self.current_inst_name + ".xml"   
                    # find the instruction and extract the bits specific to the instruction by applying filters   
                    if "iformfile" in tr.attrib and tr.attrib["iformfile"] == file_name and tr.attrib["label"] == "64-bit":                                           
                        for td in tr:
                            if td.text:
                                inst_field_values.append (td.text)
                            else:
                                inst_field_values.append ("X")
        self.create_inst_field_values_dict(inst_fields, inst_field_values)
    
    def create_inst_field_values_dict(self, inst_fields, inst_field_values):
        "\nMerging lists"
        for i in range(len(inst_fields)):
            self.inst_field_values[inst_fields[i]] = inst_field_values[i]
            print (inst_fields[i] + "::" + inst_field_values[i])
                   
    def print_dict(self):
        print ("\n\nPrinting inst_class_fields dictionary for inst " + self.current_inst_name)
        for item in self.inst_class_fields:
            print (item)
        print ("\n\n")
    
    def match_bytecode_pattern(self):
        testcase_cnt = 0
        # Loop through the extracted class fields in the dictionary and extract them for comparison with the bitstring from the pvs output file
        for field in self.inst_class_fields:
            # fields for comparing against the bitstring
            hibit = None
            lowbit=None
            name = None
            width = None
            fixed_pattern = None
            field_value = None
            compare_bit = False
            

            # field extraction from the dictionary
            hibit = int(field['hibit'])
            
            if "name" in field:
                name = field['name']
            else:
                name="not_defined"
            
            if "width" in field:
                width = int(field["width"])
            else:
                width = 1
            
            if  "fixed_pattern" in field:
                fixed_pattern = field["fixed_pattern"]
            else:
                fixed_pattern = ""
            
            if name in self.inst_field_values:
                field_value = self.inst_field_values[name]
            else:
                field_value = ""
            lowbit = hibit - width
            print ("bitstring [" + str(lowbit) + ":"  + str(hibit) + "] = " + self.current_bitstring[lowbit+1:hibit+1])
            if field_value is not "":
                print (name + "::" + str(field_value)[::-1])
            if fixed_pattern is not "":
                print (name + "::" + str(fixed_pattern)[::-1])
            # Field value needs to be reversed to make sure the pattern is compared correctly according to MSB/LSB
            if self.current_bitstring[lowbit+1:hibit+1] == field_value[::-1]:
                print ("Pattern Matched\n")
                testcase_cnt+=1
            elif self.current_bitstring[lowbit+1:hibit+1] == fixed_pattern[::-1]:
                print ("Pattern Matched\n")
                testcase_cnt+=1
            #else:
            #    print("Pattern not compared\n")
        print "Total test cases passed:" +  str(testcase_cnt)

    def convert_bitstring_to_bytecode(self):
        recreated_bytecode=""
        print "Recreating the bytecode from the current bitstring"
        current_bitstring_rev = self.current_bitstring [::-1]
        for i in range(0,32,8):
            recreated_bytecode = "%02X" %(int(current_bitstring_rev[i:i+8],2)) + recreated_bytecode
        if self.current_bytecode == recreated_bytecode.lower():
            print "Recreated bytecodes match"
        
inv = inverse_dict()
inv.parse_pvs_file("CURRENT_TIME_FFFFFFFF0001C100.pvs")
inv.parse_dec_file("CURRENT_TIME_FFFFFFFF0001C100.dec".lower())
inv.validate_instructions()
