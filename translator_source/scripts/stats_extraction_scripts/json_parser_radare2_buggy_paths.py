# usage: python cfg_json_parser.py test_output.json => test_output.json is the json file generated for a function from radare2 using the command agfj <fn_name>
# required files zircon.assembly , >input_json_file_from_radare>
import sys
import json
import re
import collections
import os
import auto_decoder_for_stats as stats
import operator
class cfg_json_parser:

    def __init__(self):
         #self.target_binary_file = "zircorn.assembly"
         #self.target_binary_file = "vmlinux"
    	 self.current_path = os.getcwd()
    	 self.input_dir = self.current_path + "/intermediate_json_files/"
    	 self.output_dir = "intermediate_dec_files/"
         #input batch file with .json filenames
         self.batch_file = sys.argv[1]                          		
         # file pointer for reading from the batch file which is the input file having names of all the .json files for every terminal function found
         self.batch_file_ptr = open(self.input_dir + self.batch_file,"r")        
         self.output_batch_file_name = self.batch_file + "_dec"
    	 self.output_batch_file_ptr = open ( self.output_dir + self.output_batch_file_name , "w")
         self.target_binary_file_ptr = None
         self.linear_fn = []
         self.looping_fn = []
         self.results_file = None
	 self.all_main_files = []
	 self.top = "TOP_" + self.batch_file.replace(".batch", "").upper() + ".pvs"
         self.output_pvs_files = "output_pvs_files/"
         # Path for stat files which hold the info related to nos and uniquesness of instructions for a fnc
         cur_dir = os.path.abspath('')
         self.stat_output_dir = cur_dir + "/output_stats_files/"
	 self.stat_output_file_name = self.batch_file.replace("batch", "txt")
         self.stat_output_file = open (self.stat_output_dir + self.stat_output_file_name, "w")
	 self.fnc_data_dict = {}
         # A map tp keep track of total unique insts and classes across all the functions 
	 self.class_map = {}
         self.inst_map = {}
         # This stores only the names of looping fnc, self.looping_fn stores names as well as loop info such as simple/complex
         self.loops_list=[]
         self.fnc_name_change_map = {}
         # A dict with key = fnc_name and value = list of unique inst classes
         self.fnc_and_classes = {}
	 self.fnc_and_inst = {}
	 # This holds the fnc name as the key and the total instruction count as the value
	 self.fnc_and_inst_cnt ={}
         # Read each line from the input batch file
         for line in self.batch_file_ptr:
             line = line.strip()
             self.input_json_file = self.input_dir + line
             self.input_json_file_ptr = open(self.input_json_file,"r")        #json_file_ptr
             self.json_obj = json.load(self.input_json_file_ptr)
             self.fnc_name = None                               # Name of the function to generate paths from CFG
             self.inst_cnt = 0                                  # nos of inst in every block
             self.blocks = []                                   # total blocks
             self.comments = []
             self.source_block = None                           # This stores the couurce block or where the cfg starts from
             self.source_block_address = None                   # This stores the couurce block addr
             self.term_blocks = []                              # This can be a list because there can be more than one terminal blocks
             self.term_blocks_addr = []                         # This stores the terminal block addr
             self.addr_list = []                                # This is a list of tuple. Each tuple hold the addr of the curr block and addr of where a jump or a fail points to. For example )xFFFFFAAAA to Ox FFFFFBBBBB                                  #
             self.path = []                                     # This holds each path that is generated during the recursive DFS on the CFG
             self.main_file = None                              # Name of the main output file generated for PVS with the control flow for each path
             self.main_file_ptr = None                          # pointer to the main output file
             self.all_possible_paths = []                       # Stores all the possible paths which have been extracted by the recursive DFS
             self.all_block_addresses = []                      # This holds all the block addresses in the fnc
             self.all_block_addr_symbols = []                   # This holds all the block addresses with the fail or jump in the function
             self.visit_completed = []                          # A list to hold all the nodes from which all loops have been searched for
             self.loop_counter = 0
             self.simple_loop_counter = 0
             self.complex_loop_counter = 0
             self.parse_json_file()
         self.print_dict()
         self.print_dict2()
	 self.print_dict3()
	 self.print_fn_dict()
		    
    # HElper method to convert to hex
    def tohex(self, val, nbits):
        return hex((val + (1 << nbits)) % (1 << nbits))
    
    # Called for each function within the file
    def parse_json_file (self):
        self.extract_fnc_name()
        self.extract_blocks()
        self.extract_blocks_for_stats()
        #self.view_addresses()
        self.discover_loops_wrapper()
    
    # Extract the function name from the corresponding .json file
    def extract_fnc_name(self):
        self.fnc_name = str (self.json_obj[0]["name"])[4:]	#
        original_fnc_name = self.fnc_name
	if self.fnc_name.startswith("__"):	
		self.fnc_name = self.fnc_name.replace("__","f__",1)
	self.fnc_name = self.fnc_name.replace("::","__")
        print "Function name::" + self.fnc_name
        self.fnc_name_change_map [self.fnc_name] = original_fnc_name
        self.inst_cnt = self.json_obj[0]["size"] / 4
        #print "inst_cnt for " + self.fnc_name + "::" + str (self.inst_cnt)
    
    def print_fnc_names_map(self):
        print ("\n\nPrinting names of functions that have changed")
        print self.fnc_name_change_map

    # Find the lines to decompile and store them ina .dec file from for the given block address
    def seek_zircon(self, block_addr, inst_in_block):
        cnt = 0
        found = False
	# Open the zircon.assembly objdump file
        self.target_binary_file_ptr = open(self.target_binary_file, "r")
        output_file_name = self.fnc_name +"_" + block_addr + ".dec"
        output_file = open(self.output_dir + output_file_name , "w")
        #print 'searching for block address in zircon file...' + str(block_addr)
        for line in self.target_binary_file_ptr:
            line = line.strip()
            tokens = re.split("\s+",line)
            if str (block_addr) in tokens[0]:
                found = True
            if found == True and cnt <= inst_in_block:
                output_file.write (line + "\n")
            #    print (line + "\n")
                if len(tokens) > 2:
                    cnt+=1
            if cnt >= inst_in_block:
                output_file.close()
                self.target_binary_file_ptr.close()
                break
        print "Generating file:" + output_file_name
      
    # Helper method to find all the blocks that jump to the current block
    def get_incoming_nodes(self, curr):
        incoming_nodes = []
        for every_tuple in self.addr_list:
            if every_tuple[1] == curr:
                incoming_nodes.append (every_tuple[0])
        return incoming_nodes

    # wrapper method for the recursive method generate_paths()
    def generate_paths_wrapper(self):
        print "Generating all possible path/s from source to destination...\n"
        for each_term_block in self.term_blocks_addr:
            self.generate_paths(self.source_block_address ,each_term_block, each_term_block)
        print self.all_possible_paths
    
    # wrapper method to call the recursive method for discovering loops
    def discover_loops_wrapper(self):
        ancestor_nodes = []
        for each_terminal in self.term_blocks_addr:
            self.discover_loops(each_terminal, each_terminal, ancestor_nodes)
        if self.loop_counter == 0:
            print "No loops found in function:" + self.fnc_name
            self.linear_fn.append(self.fnc_name)
            self.generate_paths_wrapper()
            self.generate_main()
        else:
            print "Total loops found:" + str(self.loop_counter)
            self.looping_fn.append(self.fnc_name + "::" + str(self.loop_counter) + "\tSimple loops::" + str(self.simple_loop_counter) + "\tComplex loops::" + str(self.complex_loop_counter))
            self.loops_list.append(self.fnc_name)

    # Recursive method for loop discovery
    def discover_loops(self, term, curr, ancestor_nodes):
        nodes_to_visit = self.get_incoming_nodes(curr)
        remove_list = []
        next_node = None
        # This condition checks for the loops from the current node
        for node in nodes_to_visit:
            # if any node in the list of nodes to visit is already in the stack of ancestor nodes then this is a loop because of the presence of a backedge
            if node in ancestor_nodes or node == curr:
                print "Loop discovered from node::"
                self.loop_counter += 1
                if node == curr:
                    self.simple_loop_counter +=1
                else:
                    self.complex_loop_counter +=1
                i = len(ancestor_nodes) - 1
                stop_index = ancestor_nodes.index (node)
                while i >= stop_index:
                    print ancestor_nodes[i]
                    i = i-1
                remove_list.append (node)
        # remove all the  that cause loops from the nodes to visit
        for loop_node in remove_list:
            nodes_to_visit.remove(loop_node)
        # This is the recursion where each node will be visited and all loops will be detected form the node
        while len(nodes_to_visit) > 0:
            next_node = nodes_to_visit.pop()
            if next_node in self.visit_completed:
                continue
            else:
                ancestor_nodes.append (next_node)
                self.discover_loops(curr, next_node, ancestor_nodes)
        self.visit_completed.append(next_node)
        if len(ancestor_nodes) > 0:
            ancestor_nodes.pop()
        else:
            return
    
    # Recursive method for generating all the possible linear paths from terminal block/s to the start block
    def generate_paths(self, start ,dest, curr):
        self.path.append(curr)
        if curr == start:
            new_path = list(self.path)
            self.all_possible_paths.append(new_path)
            self.path.remove(curr)
            return self.path
        incoming_nodes = self.get_incoming_nodes(curr)
        for every_node in incoming_nodes:
            self.path = self.generate_paths(start ,curr, every_node)
        self.path.remove(curr)
        return self.path
    
    # method for creating the top file which has the names of all .main files generated which is loaded into pvs for typechecking after each run
    def generate_top(self):     
        top_fp = open (self.output_pvs_files + self.top, "w")
        top_theory_name = self.top.replace (".pvs","")
        print "Generating top.pvs file : " + self.top
        top_fp.write(top_theory_name + ": THEORY" +"\n" )
        top_fp.write ("\n    BEGIN\n\n")       
        for line in self.all_main_files:
            line = line.strip()
            top_fp.write ("\n\tIMPORTING " + line.upper())
	top_fp.write ("\n\nEND " + top_theory_name ) 
        top_fp.close()    

    # Generates the .main file for each function.
    def generate_main(self):
        self.main_file = self.fnc_name + "_main"
        self.all_main_files.append(self.main_file)
        self.main_file_ptr = open(self.output_pvs_files + self.main_file.upper()  +".pvs" , "w")
        self.main_file_ptr.write(self.fnc_name.upper()+ "_MAIN " +" [ (IMPORTING arm_state) p: s ]: THEORY" +"\n" )
        self.main_file_ptr.write ("\n    BEGIN\n")
        self.main_file_ptr.write ("\n      IMPORTING")
        for index, each_block_name in enumerate(self.all_block_addresses):
            if index == 0:
                tabs = " "
            else:
                tabs = "\t\t"
            if index == len (self.all_block_addresses) -1:
                    self.main_file_ptr.write (tabs + self.fnc_name.upper() + "_" + each_block_name.upper() +"\n")
            else:
                if each_block_name == self.source_block_address:
                    self.main_file_ptr.write (tabs + self.fnc_name.upper() + "_" + each_block_name.upper()  +",\n")
                else:
                    self.main_file_ptr.write (tabs + self.fnc_name.upper() + "_" + each_block_name.upper() +",\n")
        self.main_file_ptr.write ("\n")
        idx = 0
	# loop over all the possible paths
        for path in self.all_possible_paths:
                len_path = len(path)
                self.main_file_ptr.write ("       " + self.fnc_name.upper() + "_post" + str(idx)+ " : s = ")
                for index, each_node in enumerate(path):
                    if index == 0:
                        tabs = ""
                    else:
                        tabs = "\t    "
                    if index == len_path-1:
                        if each_node == self.source_block_address:
                            self.main_file_ptr.write ( tabs + self.fnc_name.upper() + "_" + each_node.upper()+ "[p]" + "\n\t\t\t")
                        else:
                            self.main_file_ptr.write ( tabs + self.fnc_name.upper() + "_" + each_node.upper() + "\n\t\t\t")
                    else:
                        self.main_file_ptr.write ( tabs + self.fnc_name.upper() + "_" + each_node.upper() + "[" + "\n\t\t\t")
                self.main_file_ptr.write (  "\t    " )
                for index, each_node in enumerate(path):
                    if index == len(path) -1:
                        self.main_file_ptr.write (  ".B_post" )
                    else:
                        self.main_file_ptr.write (  ".B_post]" )
                self.main_file_ptr.write ("\n\n")
                idx+=1
        self.main_file_ptr.write ("\n    END " + self.main_file.upper() + "\n")  

    # Reads the .json file for each function and extracts the corresponding blocks from it
    def extract_blocks(self):
        blocks =  (self.json_obj[0]["blocks"])
        start_address = (self.json_obj[0]["offset"])
        for block in blocks:          
            block_addr_curr = None
            inst_in_block = None
            if "offset" in block:
                #print "offset:" + str(self.tohex(int (block["offset"]), 64)[:-1])[2:]
                block_addr_curr = str(self.tohex(int (block["offset"]), 64)[:-1])[2:]
                self.all_block_addresses.append (block_addr_curr)
            if start_address == block["offset"]:
                #print "Starting block address recorded"
                self.source_block_address =  block_addr_curr
            if "jump" in block:
                block_addr_true = str (self.tohex(int (block["jump"]), 64)[:-1])[2:]
                if "fail" in block:
                    temp1 = (block_addr_curr, block_addr_true , "t")
                    self.all_block_addr_symbols.append (block_addr_true + "_t")
                else:
                    temp1 = (block_addr_curr, block_addr_true , "v")
                    self.all_block_addr_symbols.append (block_addr_true + "_v")
                self.addr_list.append(temp1)

                self.source_block = block
            if "fail" in block:
                block_addr_false = str (self.tohex(int (block["fail"]), 64)[:-1])[2:]
                temp2 = (block_addr_curr, block_addr_false , "f")
                self.all_block_addr_symbols.append (block_addr_false + "_f")
                self.addr_list.append(temp2)
            if not "jump" in block and  not "fail" in block:
                self.term_blocks.append(block)
                self.term_blocks_addr.append(block_addr_curr)
            inst_in_block = block['size']/4
            output_file_name = self.fnc_name +"_" + block_addr_curr
            self.output_batch_file_ptr.write (output_file_name + "\n")
            output_file_name = self.fnc_name +"_" + block_addr_curr + ".dec"
            output_file = open(self.output_dir + output_file_name , "w")
	    block_ops  =  block["ops"]
            for item in block_ops:
	    	output_file.write (str(item["offset"]) + "\t" + str(item["bytes"]) + "\t" + str(item ["opcode"]) + "\n")
	    #self.seek_zircon(block_addr_curr, inst_in_block )

    # Reads the .json file for each function , extracts the corresponding blocks from it and decodes each hexstring to calculate stats
    def extract_blocks_for_stats(self):
	blocks =  (self.json_obj[0]["blocks"])
	start_address = (self.json_obj[0]["offset"])  
        stat_generator = stats.auto_decoder_stats(self.fnc_name)
	inst_per_fnc = 0
	for block in blocks:          
	    block_addr_curr = None
	    inst_in_block = None
	    if "offset" in block:
		#print "offset:" + str(self.tohex(int (block["offset"]), 64)[:-1])[2:]
		block_addr_curr = str(self.tohex(int (block["offset"]), 64)[:-1])[2:]
		self.all_block_addresses.append (block_addr_curr)
	    if start_address == block["offset"]:
		#print "Starting block address recorded"
		self.source_block_address =  block_addr_curr
	    if "jump" in block:
		block_addr_true = str (self.tohex(int (block["jump"]), 64)[:-1])[2:]
		if "fail" in block:
		    temp1 = (block_addr_curr, block_addr_true , "t")
		    self.all_block_addr_symbols.append (block_addr_true + "_t")
		else:
		    temp1 = (block_addr_curr, block_addr_true , "v")
		    self.all_block_addr_symbols.append (block_addr_true + "_v")
		self.addr_list.append(temp1)
		self.source_block = block
	    if "fail" in block:
		block_addr_false = str (self.tohex(int (block["fail"]), 64)[:-1])[2:]
		temp2 = (block_addr_curr, block_addr_false , "f")
		self.all_block_addr_symbols.append (block_addr_false + "_f")
		self.addr_list.append(temp2)
	    if not "jump" in block and  not "fail" in block:
		self.term_blocks.append(block)
		self.term_blocks_addr.append(block_addr_curr)
	    inst_in_block = block['size']/4
	    inst_per_fnc += inst_in_block
	    block_ops  =  block["ops"]
	    for item in block_ops:
	        stat_generator.decode_hexstring(item["bytes"])

	# Total unique instructions for the fnc
	inst_list = stat_generator.get_unique_inst_list()

	# Total unique instruction classes for the fnc
	class_list  = stat_generator.get_inst_class_list()
	
	# Write the outputs to the stats file
	self.stat_output_file.write ("\nFunction_name::" + self.fnc_name + "\n")
        self.stat_output_file.write (str(inst_list) + "\n")
        self.stat_output_file.write (str(len(inst_list)) + "\n")	
        self.stat_output_file.write (str(class_list)+ "\n")	
        self.stat_output_file.write (str(len(class_list)) + "\n")
	
	# create a tuple with the len (inst_list) and len of class_list) per fnc
	cnt_tuple = (len(inst_list), len(class_list))
	
	# add the tuple to a dictionary with key as the fnc name and value as the tuple for example <f1: (6,4)> means fnc f1 has 6 unique inst and 4 unique classes of inst
	self.fnc_data_dict[self.fnc_name] = cnt_tuple	
		
	# add the inst list and the class list to a dict that holds count across all the functions
        self.add_to_inst_dict(inst_list)
	self.add_to_class_dict(class_list)
	
	# Add to dict. This dictionary will have the fnc name as its key and list of classes/inst used by the fnc as its vale
	self.fnc_and_classes[self.fnc_name] = class_list
	self.fnc_and_inst[self.fnc_name] = inst_list

	# Adds the number of total instrcutions per function to a dict
	self.fnc_and_inst_cnt [self.fnc_name] = inst_per_fnc

    # This creates and updates a dictionary which holds the inst:count as a key value pair across all the functions
    def add_to_inst_dict(self, inst_list):
	    for item in inst_list:
		if item  not in self.inst_map:
			self.inst_map[item ] = 1
		else:
			val = self.inst_map[item ]
			self.inst_map[item ] = val + 1	

    # This creates and updates a dictionary which holds the inst_class:count as a key value pair across all the functions
    def add_to_class_dict(self, class_list):
	    for item in class_list:
	    	if item not in self.class_map:
			self.class_map[item] = 1
	    	else:
			val = self.class_map[item]
			self.class_map[item] = val + 1

    # This prints the dictionary with the fnc_names as the key and the tuple as the value. Tuple holds the inst_cnt and class_cnt per fnc
    def print_fn_dict(self):
	f = open (self.stat_output_dir + "stat_fnc_name_sorted_zircon.txt", "w")
	# sort the inst_cnt and class_cnt fn dictionary by inst_cnt
	inst_ordered = sorted(self.fnc_data_dict.items(), key=lambda x: x[1][0])
	f.write("Printing the names of functions sorted by instruction count")
	for item in inst_ordered:
		f.write (str(item) + "\n") 
	
	# sort the inst_cnt and class_cnt fn dictionary by class_cnt
	class_ordered = sorted(self.fnc_data_dict.items(), key=lambda x: x[1][1])
	f.write("\n\nPrinting the names of functions sorted by class count")
	for item in class_ordered:
		f.write (str(item) + "\n") 
	f.close()

    # This prints the fnc names and their classes
    def print_dict2(self):
	print "\n\nPrinting the overall fnc names and their classes"
	print str(self.fnc_and_classes)

    # This prints the fnc names and their classes
    def print_dict3(self):
	print "\n\n\t**** Printing the overall fnc names and their inst ****"
	print str(self.fnc_and_inst)
	print "\n\n\t**** Printing the overall fnc names and their total inst counts"
	print str(self.fnc_and_inst_cnt)

    # This prints the unique inst and unique class dict across all the functions in the input file
    def print_dict(self):
	print "\n\nPrinting the overall inst information for all the functions\n"
	for item, val in self.inst_map.iteritems():
		print item + "::" + str(val)

	print "\n\nPrinting the overall class information for all the functions\n"
	for item, val in self.class_map.iteritems():
		print item + "::" + str(val)
    
    # Prints all the block addresses in the .json file
    def show_all_block_addresses(self):
        print "All block addresses in the .json file from source block to destination block are:"
        for block in self.all_block_addresses:
                print str(block) + "\n"
    
    # Prints all paths in the .json file
    def show_paths(self):
        print "All paths in the CFG from source block to destination block are:"
        for path in self.all_possible_paths:
                print str(path) + "\n"
    
    # Helper method to view the .json file pretty printed
    def pretty_print_json(self):
         print json.dumps( self.json_obj, sort_keys=True, indent=4)

    # Prints all from/to addreses generated for each block in input json file'
    def view_addresses (self):        
        print "Starting block has address:" + self.source_block_address
        print "Terminal block has address:" + str (self.term_blocks_addr)
        #for addr in self.addr_list:
        #    print str(addr)
    
    # Prints all the linear functions
    def show_linear_fn(self):
        print "\nAll linear terminal functions are:"
        for fn in self.linear_fn:
            print fn
    
    # Prints all the looping functions
    def show_looping_fn(self):
        print "\nPrinting looping fn list"
        print str(self.loops_list)
        print "\nAll looping terminal functions with loop info are:"
        for fn in self.looping_fn:
            print fn

json_parser = cfg_json_parser()
json_parser.show_linear_fn()
json_parser.show_looping_fn()
json_parser.generate_top()
json_parser.print_fnc_names_map()

