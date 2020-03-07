# This code is used to auto generate pvs files from the corresponding xml files in ASL. for example generating add_addsub_imm.pvs from add_addsub_imm.xml
# How to run this script? Goto terminal type: python auto_translator.py log_imm  and_log_imm.xml. The file and_log_imm.xml or the equivalent file needs to be in the same folder as the script
# So the general format is python auto_translator.py <<class_name>> <<inst_name.xml>>

import xml.etree.ElementTree as ET
import sys
import json
import re
import os

class inst_family:

    def __init__(self,root):
    # This is the master file with all the diagrams for creating the abstract theories
     self.file_name = "encodingindex.xml"
     self.tree = ET.parse(self.file_name)
     self.root = self.tree.getroot()

     # argv[1[ is always the class name for example addsub_imm or log_imm etc.
     self.cmdline_input = sys.argv[1]
     self.args = re.split("\s+", self.cmdline_input)
     self.extraction_class_name = self.args[0]
     # This is the json obj which is stored as a string after the class has been extracted from the xml
     self.extracted_class =""
     self.inst_length = None
     self.file_ptr = None
     self.fields =[]
     self.theory_params=[]
     self.theory_params_optional=[]

     # This is the specific instruction file which needs to be translated
     self.inst_file_name = self.args[1]
     self.inst_tree = ET.parse(self.inst_file_name)
     self.inst_root = self.inst_tree.getroot()
     self.theory_name = self.inst_file_name.replace(".xml","")
     self.output_file = self.inst_file_name.replace(".xml",".pvs")
     self.proof_strategy = None
     self.ASL2PVS_types_map = []	# List for translating the declaration part from ASL to PVS
     self.ASL2PVS_fncnames_map = []	# List for translating the function names in the declaration part from ASL to PVS

    def displayRoot(self):
         print self.root.attrib

    def view_fields(self):
         print "Showing fields"
         print self.fields

    def generate_pvs_code(self):
        cur_dir = os.path.abspath('')
        self.file_ptr = open(cur_dir +"/" + self.output_file,"w")
        self.extract_field()
        self.generate_theory_name()
        self.generate_inst_diagram_pvs()
	self.generate_declarations()
        #self.generate_const_declaration_pvs()
        self.end_theory()

    def generate_theory_name(self):
        arm_state_param = "(IMPORTING arm_state) p: s"
        theory_param=""
        self.file_ptr.write(self.theory_name +"[" + arm_state_param+ theory_param +"]" + ":THEORY\n")
        #"[imm:bvec[12],rn:string,rd:string ]
        self.file_ptr.write("\n\tBEGIN\n")

        # A generic helper method to return the name and type of a field as a string in pvs. For example, Diag: bvec[32]. Optional arguments to specify the length
    def create_pvs_var_unspecified(self, var_name, var_type, *positional_parameters, **keyword_parameters):
            pvs_var = ""
            option = ""
            if ('length' in keyword_parameters):
                option = "[" + keyword_parameters['length'] + "]"
            pvs_var = var_name + ": " + var_type + option
            return pvs_var

    def create_pvs_var_proof(self, var_name, var_type, *positional_parameters, **keyword_parameters):
            pvs_var = ""
            option = ""
            if ('length' in keyword_parameters):
                option = "(" + keyword_parameters['length'] + ")):false"
            pvs_var = var_name + ":= " + var_type + option   # Amer used to be " : " this is a syntax error here in pvs.
            return pvs_var

    def create_pvs_var_specified(self, var_name, var_type, *positional_parameters, **keyword_parameters):
                pvs_var = ""
                option = ""
                if ('value' in keyword_parameters):
                    option = " = " + keyword_parameters['value']
                pvs_var = var_name + ": " + var_type + option
                return pvs_var


    def create_pvs_record_type(self, param_list):
        record_type ="[# "
        for x in param_list:
            if record_type == "[# ":
                record_type = record_type  +  x
            else:
                record_type = record_type + ", " + x
        record_type = record_type + " ,length: {n: nat|n = 32} #]" # Amer: used to be n=32, give two spaces around equality to avoid some errors in pvs7
        #print record_type
        return record_type

    # method to autogenerate a proof to embed in the .pvs file for typechecking. It uses the regdigram fields
    def create_pvs_proof(self, param_list):
        record_type ="(inst 1 \"(#"
        cnt = 0
        for x in param_list:
            if cnt == 0:
                record_type = record_type + " " + x
            else:
                record_type = record_type + ", " + x
            cnt+=1
        record_type = record_type + ", length:= 32 #)\")" # Amer: used to be length: = 32, the space here is an error.

        return record_type

    # Auto-generates the diagram from the xml file to the pvs
    def generate_inst_diagram_pvs(self):
        print "Translating file:"
        self.file_ptr.write("\n\t" + self.create_pvs_var_unspecified("Diag","bvec", length = "32"))
        self.file_ptr.write("\n\t" + self.create_pvs_var_unspecified("addr","nat"))
        self.file_ptr.write("\n\tIMPORTING bts[32], bt[32]\n")
        #diag_record_type = "[# sf: bvec[1],  op: bvec[1], S: bvec[1], fixed<num>: bvec[5], shift: bvec[2], imm12: bvec[12], Rn: bvec[5], Rd: bvec[5], length: {n:nat|n=32}  #]"
        field_decl_list =self.generate_field_declaration_pvs()
        #print "field list:" + str(field_decl_list)
        diag_record_type = self.create_pvs_record_type(field_decl_list)
        proof_fields_list = self.generate_proof_fields_pvs ()
        self.proof_strategy = self.create_pvs_proof(proof_fields_list)
        self.file_ptr.write("\n\t" + self.create_pvs_var_specified("diag","Type+",value = diag_record_type))
        self.file_ptr.write("\n\t" + self.create_pvs_var_unspecified("D","diag"))
        self.file_ptr.write("\n\t" + self.generate_diagram_init() +"\n")
        self.file_ptr.write("\n%|- diag_TCC* : PROOF "+ self.proof_strategy  +" QED\n") # Amer: used to be _TCC* , PROOF (" , ") QED. These are illegal for this tccs, thus modified! \t here does not follow pvslite community style.
        self.file_ptr.write("\n\t%ASL constants declarations\n")



    # helper function to generate a list of fields that constitute the 32 bit ARM diagram
    def generate_field_declaration_pvs(self):
        field_decl_list =[]
        fixed_cntr = 1
        for x in self.fields:
            field_type = "bvec"
            if 'name' in x:
                field_name = x['name']
                if field_name == 'cond':
                    field_name = 'cond_ '
                if field_name == "Rn":
                    field_name_modified = "xn_sp"
                if field_name == "Rd":
                    field_name_modified = "xd_sp"
            else:
                field_name = 'Fixed' + str(fixed_cntr)
                fixed_cntr +=1
            if 'width' in x:
                bvec_len = x['width']
            else:
                bvec_len = "1"
            field_decl = self.create_pvs_var_unspecified(field_name, field_type, length = bvec_len)
            field_decl_list.append(field_decl)
        return field_decl_list

    # helper function to generate a list of fields that constitute the 32 bit ARM diagram
    def generate_proof_fields_pvs(self):
        field_decl_list =[]
        fixed_cntr = 1
        for x in self.fields:
            field_type = "lambda(i:below"
            if 'name' in x:
                field_name = x['name']
                if field_name == "cond":
                    field_name = 'cond_'
                if field_name == "Rn":
                    field_name_modified = "xn_sp"
                if field_name == "Rd":
                    field_name_modified = "xd_sp"
            else:
                field_name = 'Fixed' + str(fixed_cntr)
                fixed_cntr +=1
            if 'width' in x:
                bvec_len = x['width']
            else:
                bvec_len = "1"
            field_decl = self.create_pvs_var_proof(field_name, field_type, length = bvec_len)
            field_decl_list.append(field_decl)
        return field_decl_list

   

    def var_initialize_pvs(field_name, field_type, *positional_parameters, **keyword_parameters):
        pvs_var = ""
        option = ""
        if ('length' in keyword_parameters):
            option = "[" + keyword_parameters['length'] + "]"
        pvs_var = field_name + ":= " + field_type + option
        #print pvs_var

    # obsolete helper function to generate a list of fields that constitute the 32 bit ARM diagram
    def generate_field_initialization_pvs(self):
            field_decl_list =[]
            fixed_cntr = 1
            for x in self.fields:
                field_type = ""
                if 'name' in x:
                    field_name = x['name']
                else:
                    field_name = 'Fixed' + str(fixed_cntr)
                    fixed_cntr +=1
                if 'width' in x:
                    bvec_len = x['width']
                else:
                    bvec_len = "1"
                field_decl = self.var_initialize_pvs(field_name, field_type)
                field_decl_list.append(field_decl)
            #print field_decl_list

    ###TODO:some fields do not have width parameter even if the length is 1
    def generate_diagram_init(self):
        str1 = "v: diag = D with [ "
        str4 =""
        str2 = ""
        theory_type = ""
        fixed_cntr = 1
        for x in self.fields:
            hibit = x['hibit']
            lowbit =""
            if 'name' in x:
                field_name = x['name']
                if field_name == 'cond':
                    field_name = 'cond_'

            else:
                field_name = 'Fixed' + str(fixed_cntr)
                fixed_cntr +=1
            if 'width' in x:
                theory_type = "bts"
                lowbit_int = int(hibit) - int(x['width']) + 1
                lowbit =  str(lowbit_int) + ", " # Amer: used to be the otherway around, that is unsound. Now it PVS decession precedures can will not generete the v_TCCs at all!
            else:
                #print str(x) + "::bt"
                theory_type = "bt"
            str2 = str2 + field_name + ":= " +  theory_type  + "(Diag, "+  lowbit + hibit + " ) ," #
            #print str2
        str3 = ' length:= 32 ]'
        str4 = str1 + str2 + str3
        return str4

    # This method auto-generates the declarations in the operational part 
    def generate_declarations(self):
   	ASL2PVS_fncnames_map = {}
	ASL2PVS_types_map = {}
	f = open ("sample.txt", "r")
	# Read each line from the input file or dictionary whihc stores the extracted ASL declarations
	for line in f:
		PVS_TYPE = ""
		PVS_fnc = ""
		conversion_fnc = ""
		extracted_field = ""
		line = line.strip()[:-1] 	# remove ;
		# Extract the field/s within the "()" in the ASL. For example "(Rd)" or "(op == '1')" => op == '1'		
		if "(" and ")" in line:
			paren_start = line.find("(")
			paren_end = line.find (")")
			extracted_field = line [paren_start+1: paren_end]				
		tokens = re.split("\s+", line)
		ASL_TYPE = tokens [0]
		type_name = tokens [1]
		operator = tokens [2]	
		# Find the token which has "()"
		for token in tokens:
			parenthesis_idx = token.find("(")
			# Extract the name before "(" such as "Uint" in "Uint(Rd)"
			if parenthesis_idx > 0:  # Uint( or <no fnc>( op == "1")
				conversion_fnc = token[:parenthesis_idx]

		# Check the ASL_fnc_names dictionary if a fnc is present and return the PVS fnc if present else add it as a new type
		if conversion_fnc  in ASL2PVS_fncnames_map:
			PVS_fnc = ASL2PVS_fncnames_map[conversion_fnc]
		else:
			if conversion_fnc == "UInt":
				PVS_fnc = "bv2nat"
				ASL2PVS_fncnames_map [conversion_fnc] = PVS_fnc
		# Check the ASL_types dictionary if a type is present and return the PVS type if present else add it as a new type
		if ASL_TYPE in ASL2PVS_types_map:
			PVS_TYPE = ASL2PVS_types_map[ASL_TYPE]
		else:
			if ASL_TYPE == "integer":
				PVS_TYPE = "int"
				ASL2PVS_types_map[ASL_TYPE] = PVS_TYPE
			if ASL_TYPE == "boolean":
				PVS_TYPE = "bool"
				ASL2PVS_types_map[ASL_TYPE] = PVS_TYPE
		# Adding the translation to the output pvs file	
		if PVS_TYPE == "int":
			if type_name == "datasize":
                                self.file_ptr.write("\n\t" + type_name + " : " + PVS_TYPE + " " + " " + operator + " 64")
			else:
                                self.file_ptr.write("\n\t"+ type_name + " : " + PVS_TYPE + " " + operator + " " + PVS_fnc + " (" + extracted_field +")")
		if PVS_TYPE == "bool":
			field_tokens = re.split("\s+", extracted_field)
			# TODO Check if the name of the variable in token[1] belongs to the diagram, in that case add v otherwise just use the token [0] name
			field_tokens [0] = "v'" + field_tokens[0] 	
			field_tokens [1] = field_tokens [1].replace("==", " = ")
			field_tokens [2] =  "bv ( 0b"  + field_tokens [2].replace ("'", "") + " )"
			new_fields = field_tokens [0] + field_tokens [1] + field_tokens [2]
			self.file_ptr.write("\n\t"+ type_name + " : " + PVS_TYPE + " "  + operator  + " (" + " " + new_fields + " )")

    def view_fields(self):
        generic_theory_string = ''
        for x in self.fields:
            print x

    # fields is a dictionary that keeps track of each field in the xml. the xml tag has the name 'box'. Each field is added to the list self.fields
    def extract_field(self):
         for node in self.extracted_class.findall(".//regdiagram"):
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


    # This method extracts the types of parameters for a particular theory whether they are optional parameters like shift or Xn_SP and Xd_SP
    def extract_theory_parameters(self):
        for node in self.inst_root.findall('.//encoding'):
             if node.attrib["label"]=="64-bit":
                 for childnode in node.findall('.//asmtemplate'):
                        for child in childnode:
                            if child.tag=="a":
                                if re.search(r'\boptional\b', child.attrib['hover'], re.I):
                                    self.theory_params_optional.append(child.attrib['link'])
                                else:
                                    self.theory_params.append(child.attrib['link'])

    def extract_declarations(self):
	 print "Extracting"
	 for node in self.inst_root.findall('.//pstext'):
		node.tail
		for child in node:		
			if 'hover' in child.attrib:
				var = re.split("\s+", child.attrib['hover'])[0]
				
				print  "\n"+ child.attrib['hover'] + "\nPath:    /ISA_v83A_A64_xml_00bet5/shared_pseudocode.xml#" + child.attrib['link']
				#print "Text:\t" + child.text
				#print "Tail:\t" + re.split(";",child.tail)[0]


    def extract_inst_class(self):
        for node in self.root.findall('.//iclass_sect'):
            #print node.attrib
            if node.attrib['id'] == self.extraction_class_name:
                self.extracted_class = node

    def view_inst_class_names(self):
        print "Displaying all class names for ARM64 instruction set from ASL..."
        for node in self.root.findall('.//iclass_sect'):
            print node.tag  

    def end_theory(self):
        self.file_ptr.write ("\n\t  post: s = p")
        #print 'END ' + self.theory_name
        self.file_ptr.write ('\nEND ' + self.theory_name +' \n')

    def view_extracted_diagram(self):
        for child in self.extracted_class.find("regdiagram"):
                print child.attrib


inst_imm = inst_family('')
inst_imm.extract_inst_class()
inst_imm.extract_theory_parameters()
inst_imm.view_fields()
inst_imm.generate_pvs_code()
inst_imm.extract_declarations()
#inst_imm.generate_field_initialization_pvs()
