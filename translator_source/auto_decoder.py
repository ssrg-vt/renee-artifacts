# Usage example python auto_decompiler.py target.dec
# Generates a main.pvs file which is the controller


import xml.etree.ElementTree as ET
import sys
import json
import re
import collections
import time
import os
import ctypes
import subprocess

class auto_decompiler:

    def __init__(self,root):
        # This is the master file with all the diagrams for creating the abstract theories
         self.current_path = os.getcwd().strip() +"/"
         self.output_dir = "output_pvs_files/"        
         self.input_batch_file_name =  sys.argv[1]
         self.input_dir = "/assets/intermediate_dec_files/"
         self.input_batch_file_ptr = open (self.current_path +  self.input_dir + self.input_batch_file_name, "r")
         #Supporting input file section
         self.ASL_files_dir = "/assets/ASL_xml_files/"
         self.file_name = "encodingindex.xml"
         self.file_ptr = open(self.current_path + self.ASL_files_dir + self.file_name,"r")
         path = self.current_path + self.ASL_files_dir
         os.listdir(path)
         fullname = os.path.join(path, self.file_name)
         self.tree = ET.parse(fullname)
         self.root = self.tree.getroot()
         #self.class_to_decode = sys.argv[2]
         self.inst_addr = None
         self.bitstring = ""
         # I/O for the script
         self.inst_length = None
         # Data structures for the class
         self.fields =[]         # This list stores all fields from the regdiagram which have a name
         self.decode_fields = [] # This list only stores the fields which are required to decode it to the instructions belonging to the class
         self.top_level_nodes = []
         self.class_signature = []
         self.inst_signature = [] # This list holds the dna for each instruction which will be pivkled
         self.inst_counter = 0
         self.cur_group_node = None
         self.cur_class_node = None
         self.cur_inst_node = None
         self.block_code = None
         self.jump = None
         self.fail = None
         # This field holds the final pvs instruction
         self.last_pvs_inst="p0"
         self.comments = []
         self.empty_str = ''
	 
	 # read every line from the batch dec file which holds all the information about the .dec files generated
         for line in self.input_batch_file_ptr:
            self.binary_file = line.strip()
            self.binary_file_ptr = open(self.current_path + self. input_dir + self.binary_file + ".dec","r")
            #print "\n\nFilename::" + self.binary_file
            # Rename files that start with __ with f__ and that contain :: with __
	    if self.binary_file.startswith("__"):	
	    	self.binary_file = self.binary_file.replace("__","f__",1)
	    self.binary_file = self.binary_file.replace("::","__")
            self.theory_name = self.binary_file.upper()
            self.decompile_binary()

    def flush_all(self):
         self.cur_group_node = None
         self.cur_class_node = None
         self.cur_inst_node = None
         self.inst_addr = None
         self.bitstring = ""
         self.class_signature = []
         self.inst_signature = [] #
         self.inst_length = None
         # Data structures for the class
         self.fields =[]         # This list stores all fields from the regdiagram which have a name
         self.decode_fields = []
         self.jump = None
         self.fail = None


    # Main method for decompiling the binary into the corresponding ARM instructions
    def decompile_binary(self):
	self.inst_counter = 0
        self.extract_top_level_nodes()
        cnt = 0
        self.output_file_name = (self.binary_file.replace(".dec", "").upper() +'.pvs')
        self.output_file=open(self.output_dir + self.output_file_name,"w")
	
	# Read each line from the .dec file 
        for line in self.binary_file_ptr:
            comment_flag = False
            line = line.strip()
            self.line = line
            if '%' in line:
                self.comments.append (line)
                comment_flag = True
                #print "\t\tDEAD CODE 1"
            else:
                binary_strings = re.split("\s+", line)
                len_bs =  len (binary_strings) # len_bs can be either 2 or 4+ depending on if it is a function name or an instruction
                # if the line is not a comment and the first line after the comments or the first line in the file
                if cnt == 0:
                    # Create a new pvs theory for the first line in the file
                    self.generate_pvs_theory()
                if len_bs > 2 :
                    self.flush_all()
                    #print "********************************* Decoding next instruction ***********************************************\n"
                    self.inst_addr = int(binary_strings [0])#[:-1], 16)
                    #print self.inst_addr
                    #print binary_strings [1]
		    hexstring = binary_strings [1] [6:8]+binary_strings [1] [4:6]+binary_strings [1] [2:4]+binary_strings [1] [0:2]
                    #hexstring = binary_strings [1] #[6:8]+binary_strings [1] [4:6]+binary_strings [1] [2:4]+binary_strings [1] [0:2]
                    self.bitstring = str(bin(int(hexstring,16)))[2:]
                    self.bitstring = self.bitstring.zfill(32)
                    #print self.bitstring
                    #print len(self.bitstring)
                    # for branching instructions extract the jump values from the .dec file
                    jump = binary_strings[2].split("_")[1]
                    fail = binary_strings[3].split("_")[1]
                    if jump is not self.empty_str:
                        self.jump = subprocess.check_output(["rax2", str(jump)])
                        self.jump =  self.jump.replace("\n","")
                    if fail is not self.empty_str:
                        self.fail = subprocess.check_output(["rax2", str(fail)])
                        self.fail =  self.fail.replace("\n","")
                    self.decode_group_level()
                    #self.view_cur_group_node()
                    self.extract_classes_from_group()
                    #self.view_class_signature()
                    self.decode_class_level()
                    self.extract_insts_from_class()
                    #self.view_inst_signature()
                    self.decode_inst_from_class()
                if len_bs < 2:
                    continue
                    print "\t\tDEAD CODE 3"
                cnt +=1
        self.generate_end_theory()
        print 'Generating...' + self.output_file_name      

    # Helper method for debugging
    def displayRoot(self):
         print self.root.attrib


    # This mehtod displays the auto_extracted fields from the reg_diagram
    def view_fields(self):
         #print '\nInside  view_fields.... \n'
         for field_tuple in self.fields:
             print str(field_tuple)
    
    # Helper method 
    def view_decode_fields(self):
         #print '\nInside  view_decode_fields.... \n'
         for field_tuple in self.decode_fields:
             print str(field_tuple)
    
    # Helper method 
    def view_class_signature(self):
          print '\nDisplaying decode table at the group level  (view_class_signature) ...\n'
          for inst in self.class_signature:
             print str(inst)

    def view_inst_signature(self):
          print '\nDisplaying decode table at the class level  (view_inst_signature) ...\n'
          print "\nClass decoded for the bitstring:" + self.bitstring + "\tclass = " + str(self.cur_class_node) + "\n"
          for inst in self.inst_signature:
             print str(inst)

    # This is a helper method to view the top level nodes in the encoding xml which gives the groups of instructions
    def view_top_level_nodes(self):
            print '\nTop level encoding for A64 after extraction..\n'
            for node in self.top_level_nodes:
                print node.attrib
                for child in node:
                    if child.tag == 'decode':
                        for box in child:
                            print box.attrib
                            for c in box:
                                print c.text

    # This is a helper method to view the group of instruction selected
    def view_cur_group_node(self):
        print "Group decoded for the bitstring:" + self.bitstring
        print "Group_name = " +  str(self.cur_group_node.attrib)

    # This is a helper method to view the group of instruction selected
    def view_cur_class_node(self):
        print "\nClass decoded for the bitstring:" + self.bitstring + "\tclass = " + str(self.cur_class_node)

    # This method extracts the top level nodes in the encoding.xml which helps to parse the binary string and compare against these extracted nodes for patterns
    def extract_top_level_nodes(self):
        for node in self.root.findall(".//node"):
            if 'iclass' in node.attrib and node.attrib['iclass'] == 'UNALLOCATED_10':
                self.top_level_nodes.append(node)
            if 'groupname' in node.attrib:
                self.top_level_nodes.append(node)

    # This is the top level check for a binary string which determines which of the 6 group of ARM instruction does the string represent.
    def decode_group_level(self):
        #print "\nInside decode instruction group...."
        xml_string = ""
        for node in self.top_level_nodes:
            for child in node:
                if child.tag == 'decode':
                    for box in child:
                        #This represents the slice of the bitstring which needs to be compared with the top level encodings to decode the group of instructions
                        top_level_check = self.bitstring[-29:-25] # Currently this number is hard-coded
                        for c in box:
                            xml_string = c.text
                            #print "xml_string:" + xml_string + "top_level_check:" + top_level_check
                            if (self.compare_bits(xml_string, top_level_check)) == True:
                                self.cur_group_node = node
        #self.view_cur_group_node()

    
    def extract_classes_from_group(self):
        #print "\nInside extract_classes_from_group.... "
        for child_node in self.cur_group_node:
            inst_list = []
            if child_node.tag == 'node':
                #print "\nNew instruction class************"
                inst_list.append(child_node.attrib['iclass'])
                for child_decode in child_node:
                    if child_decode.tag == 'decode':
                        for child_box in child_decode:
                            #print "\nNew box"
                            box_list = []
                            #print child_box.attrib
                            box_list.append(child_box.attrib['name'])
                            box_list.append(child_box.attrib['hibit'])
                            box_list.append(child_box.attrib['width'])
                            for child_c in child_box:
                                #print child_c.text
                                box_list.append(child_c.text)
                            #print str(box_list)
                            inst_list.append(box_list)
                        self.class_signature.append(inst_list)
        #print "All classes extracted for group:" + str(self.cur_group_node.attrib['groupname'])
    
    def decode_class_level(self):
            #print "\nInside decode_class_level:" + self.bitstring
            for inst in self.class_signature:
                #print "\nNext instruction:" + inst[0]
                field_num = len (inst)
                match_cntr = 0
                fields_to_match = field_num - 1 # Total number of matches required
                for x in range(1, field_num):
                    field = inst[x]
                    field_name =  field [0]    # field name such as sf
                    #print field_name
                    field_pos = int(field [1]) +1  # field position 31 negative index is used for starting from left
                    field_width = int (field [2]) # field width
                    field_pattern =  field [3]  # pattern to compare against
                    upper_bound = - field_pos # since we use negative indexes
                    lower_bound = upper_bound + field_width
                    #print upper_bound
                    #print lower_bound
                    bitstring_slice = ""
                    if field_width == 1:
                        bitstring_slice = self.bitstring[upper_bound]
                    else :
                        bitstring_slice = self.bitstring[upper_bound: lower_bound]
                    #print str(field_pattern)  + ":::" + str(bitstring_slice)
                    if self.compare_bits(str(field_pattern) ,str(bitstring_slice))  or field_pattern is None:
                        #print "Sequence matched"
                        match_cntr +=1
                        #print "Total matches:" + str(match_cntr)
                    else:
                        break
                    if match_cntr == fields_to_match:
                        #print "Class for the bitstring:" + self.bitstring
                        #print "Class name:" + inst[0]

                        self.cur_class_node = inst[0]
     
    # This extracts all the instructions needed from each class for the given group to which the instrtuction belongs  and stores it in a data structure 
    def extract_insts_from_class(self):
        #print "Inside extract_class_level_nodes:" + self.cur_class_node
        for node in self.root.findall('.//iclass_sect'):
             ###if node.attrib["id"]==self.class_to_decode:
             if node.attrib["id"]==self.cur_class_node:
                 #print "success"
                 for childnode in node:
                     if childnode.tag == 'regdiagram':
                         self.extract_class_regdiagram(childnode)
                     if childnode.tag == 'instructiontable':
                        self.extract_class_inst_fields(childnode)
                        self.create_instruction_signature(childnode)
                 break


    # This is  the second level check which determines which class of instructions within a group does an instruction belong to
    def extract_class_regdiagram(self, node):
        #print "Regdiagram details:"
        self.inst_length = node.attrib['form']
        name = None
        for box_regdiagram in node:
            if box_regdiagram.tag =='box':
                field_name = ""
                hibit_int = None
                lowbit_int = None
                width = None
                #
                if 'name' in box_regdiagram.attrib:
                    field_name = box_regdiagram.attrib['name']
                    hibit_int = int(box_regdiagram.attrib['hibit'])
                    if 'width' in box_regdiagram.attrib:
                        width = int(box_regdiagram.attrib['width'])
                        lowbit_int = hibit_int - width + 1
                    else:
                        width = 1
                        lowbit_int = hibit_int
                # create a tuple for each field such as sf in the regdiagram
                    regdiagram_field_tuple = tuple((field_name, hibit_int, lowbit_int, width))
                    self.fields.append(regdiagram_field_tuple)

    def extract_class_inst_fields(self, node):
        #print '\nInside extract_class_inst_fields... fields extracted'
        # Every node has the tag instruction tablr.
        for child in node:
            if child.tag =='thead':
                # We need to extract tr tag with "head"ing2" attrib
                for child_tr in child:
                    if child_tr.tag =='tr' and child_tr.attrib['id'] == 'heading2':
                        for child_th in child_tr:
                            self.set_field (child_th.text)    # helper method that setS the False field in the tuple to True


    # This extracts the fields form self.fields and puts them ina new list which will be used for decoding the instructions at the class level
    def set_field (self, class_field):
            for field in self.fields:
                if class_field == field [0]:
                    list_field = list (field)
                    t = tuple (list_field)
                    self.decode_fields.append(t)


    # This creates the instruction decoder which will be pickled and used at runtime. It does the final step of the extraction process from the xml.
    def create_instruction_signature (self, node):
            #print '\nInside create_instruction_signature...signature created'
            # Every node has the tag instruction table.
            for child in node:
                if child.tag =='tbody':
                      # This holds all the information for decoding each individual instruction
                    # We need to extract tr tag with "head"ing2" attrib
                    for child_tr in child:
                        inst_info = []
                        if child_tr.tag =='tr':
                            #print child_tr.attrib['encname']
                            inst_info.append (child_tr.attrib['encname'])
                            # This condition handles the unallocated inst which have no corresponding x,l file
                            if 'iformfile' in child_tr.attrib:
                                #print child_tr.attrib['iformfile']
                                inst_info.append (child_tr.attrib['iformfile'])
                            else:
                                inst_info.append ("not_implemented") # generate an exception. Unallocated
                            # This variable is used to keep track of the number of fields that make up the
                            #signature of the instruction for a particular class sich as sf,op,shift etc
                            field_counter = 0
                            # Extract the string values for each instruction for a particular field and store them in the inst signature
                            for child_td in child_tr:
                                if child_td.attrib['class'] == 'bitfield':
                                    temp = list (self.decode_fields [field_counter])
                                    temp.append (child_td.text)
                                    #print str (temp)
                                    inst_info.append (temp)
                                    field_counter+=1
                        self.inst_signature.append(inst_info)
  

    # Format of inst signature is as follows ['RET_64R_branch_reg', 'ret.xml', ['opc', 24, 21, 4, '0010'], ['op2', 20, 16, 5, '11111'], ['op3', 15, 10, 6,    '000000'],   ['Rn', 9, 5, 5, None], ['op4', 4, 0, 5, '00000']]
    def decode_inst_from_class(self):
        for inst in self.inst_signature:
            field_num = len (inst)
            match_cntr = 0
            fields_to_match = field_num - 2 # Total number of matches required
            for x in range(2, field_num):
                field = inst[x]
                field_name =  field [0]    # field name such as sf
                field_pos = -int (field [1] +1)  # field position 31 negative index is used for starting from left
                field_width =  field [3] # field width
                field_pattern =  field [4]  # pattern to compare against
                upper_bound = field_pos
                lower_bound = upper_bound + field_width
                bitstring_slice = ""
                if field_width == 1:
                    bitstring_slice = self.bitstring[upper_bound]
                else :
                    bitstring_slice = self.bitstring[upper_bound: lower_bound]
                #if field_pattern.find("!=") == True:
                #    print "anomaly!!!!!!!!!!!!!!!!!!!!!!!!!!"
                if field_pattern is None:
                    match_cntr +=1
                else:
                    if field_pattern.find("!=") == -1:
                        matched = self.compare_bits(str(field_pattern) ,str(bitstring_slice))
                        if matched == True:
                            match_cntr +=1
                    else:
                        matched = self.compare_bits(str(field_pattern[3:]) ,str(bitstring_slice))
                        if matched == False:
                            match_cntr +=1
                if match_cntr == fields_to_match:
                    #print "\nInstruction decoded for the bitstring:" + self.bitstring
                    #print inst[0] + "\t" + self.cur_class_node
                    #print "Instruction filename:" + inst[1] + "\n"
                    self.add_inst_to_file (inst[1].replace(".xml",""))       ## DO NOT REMOVE This comes form the name of the xml ASL file
                    ASL_file = inst[1]
                    #self.translator_file_ptr.write (self.cur_class_node + "\t " + ASL_file +"\n")
                    self.inst_counter+=1
                    return

    #  This method is used to create the .pvs file for the corresponding basic block .dec file #b_uncond
    def add_inst_to_file(self, var):
        previous_inst = self.last_pvs_inst
        self.last_pvs_inst = var+'_' + str(self.inst_counter)
        temp = self.last_pvs_inst
        #addr = ctypes.c_ulong(self.inst_addr).value
        addr=subprocess.check_output(["rax2", str(self.inst_addr)])
        addr = addr.replace("\n","")
        

        if self.inst_counter == 0:
            #if "b_uncond" in temp:
            if self.fail is not None:
                self.output_file.write ('    '+ "{:<19}".format(temp) + ' : Theory =    '  + "{:<18}".format(var) + '[ ' + "{:<24}".format("p0") + "{:<4}".format(' ]') +'{{Diag:= '+ 'bv [32] ( 0b' + self.bitstring  + ' ) , addr:= ' +  str(addr) + ' ,next:= ' + str(self.jump) + ' ,fail:= ' + str(self.fail) + ' }}\n')
            elif self.jump is not None: 
                self.output_file.write ('    '+ "{:<19}".format(temp) + ' : Theory =    '  + "{:<18}".format(var) + '[ ' + "{:<24}".format("p0") + "{:<4}".format(' ]') +'{{Diag:= '+ 'bv [32] ( 0b' + self.bitstring  + ' ) , addr:= ' +  str(addr) + ' ,next:= ' + str(self.jump) + ' }}\n')
            else:
                self.output_file.write ('    '+ "{:<19}".format(temp) + ' : Theory =    '  + "{:<18}".format(var) + '[ ' + "{:<24}".format("p0") + "{:<4}".format(' ]') +'{{Diag:= '+ 'bv [32] ( 0b' + self.bitstring  + ' ) , addr:= ' +  str(addr) + ' }}\n')
        else:
            #if "b_uncond" in temp:
            if self.fail is not None:
                self.output_file.write ('    '+ "{:<19}".format(temp) + ' : Theory =    '  + "{:<18}".format(var)+ '[ ' + "{:<24}".format(previous_inst + '.post') + "{:<4}".format(' ]')+'{{Diag:= '+ 'bv [32] ( 0b' + self.bitstring  + ' ) , addr:= ' +  str(addr) + ' ,next:= ' + str(self.jump) + ' ,fail:= ' + str(self.fail) + ' }}\n')
            elif self.jump is not None:
                self.output_file.write ('    '+ "{:<19}".format(temp) + ' : Theory =    '  + "{:<18}".format(var)+ '[ ' + "{:<24}".format(previous_inst + '.post') + "{:<4}".format(' ]')+'{{Diag:= '+ 'bv [32] ( 0b' + self.bitstring  + ' ) , addr:= ' +  str(addr) + ' ,next:= ' + str(self.jump) + ' }}\n')
            else:
                self.output_file.write ('    '+ "{:<19}".format(temp) + ' : Theory =    '  + "{:<18}".format(var)+ '[ ' + "{:<24}".format(previous_inst + '.post') + "{:<4}".format(' ]')+'{{Diag:= '+ 'bv [32] ( 0b' + self.bitstring  + ' ) , addr:= ' +  str(addr) + ' }}\n')

    # This method generates the header of the .pvs file
    def generate_pvs_theory(self):
 	self.output_file.write ( self.theory_name + '[ ( IMPORTING arm_state ) p : s ] : THEORY \n')
        self.output_file.write ('\n    BEGIN \n\n')
        for comment in self.comments:
            self.output_file.write ("    " + comment + "\n")
        self.output_file.write('\n    p0: s = init %  p\n\n')
    
    # This method generates the end theory
    def generate_end_theory(self):
        self.output_file.write ('\n    B_post: s = ' + self.last_pvs_inst +'.post\n')
        self.output_file.write('\n    %|- *_TCC*: PROOF (eval-formula) QED\n')
        self.output_file.write ('\nEND ' + self.theory_name)

    # This is a helper method to compare the bitsring sub-sequence with an xml sequence. A custom method is written to handle the 'x'- dont care condition
    def compare_bits(self,xml_string, binary_string):

        for(xml_bit, binary_bit) in zip (xml_string, binary_string):
            if (xml_bit != binary_bit) and (xml_bit !="x"):
                return False
        return True

auto_decompiler = auto_decompiler('')
