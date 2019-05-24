# usage: python cfg_json_parser.py test_output.json => test_output.json is the json file generated for a function from radare2 using the command agfj <fn_name>
# required files zircon.assembly , >input_json_file_from_radare>


import sys
import json
import re
import collections
import os

class cfg_json_parser:

    def __init__(self):
    	 self.current_path = os.getcwd()
    	 self.input_dir = self.current_path + "/assets/intermediate_json_files/"
    	 self.output_dir = "/assets/intermediate_dec_files/"
         self.batch_file = sys.argv[1]                          		 #input batch file with .json filenames
         self.batch_file_ptr = open(self.input_dir + self.batch_file,"r")        #json_file_ptr for batch input file
         self.output_batch_file_name = self.batch_file + "_dec"
    	 self.output_batch_file_ptr = open ( self.current_path + self.output_dir + self.output_batch_file_name , "w")
         #self.target_binary_file = "zircorn.assembly"
         self.target_binary_file_ptr = None
         self.linear_fn = {}
         self.looping_fn = []
         self.results_file = None
         self.output_pvs_files = "output_pvs_files/"
         for line in self.batch_file_ptr:
             line = line.strip()
             self.input_json_file = self.input_dir + line
             self.input_json_file_ptr = open(self.input_json_file,"r")        #json_file_ptr
             self.json_obj = json.load(self.input_json_file_ptr)
             self.fnc_name = None                               # Name of the function to generate paths from CFG
             self.inst_per_fnc = 0                          # Number of inst per fnc "ninstr"
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
             # fnc calls from init
             self.parse_file()

    def tohex(self, val, nbits):
        return hex((val + (1 << nbits)) % (1 << nbits))

    def parse_file (self):
        self.extract_fnc_name()
        self.extract_blocks()
        self.view_addresses()
        self.discover_loops_wrapper()
        #self.show_paths()

    def extract_fnc_name(self):
        self.fnc_name = str (self.json_obj[0]["name"])[4:]	
	if self.fnc_name.startswith("__"):	
		self.fnc_name = self.fnc_name.replace("__","f__",1)
	self.fnc_name = self.fnc_name.replace("::","__")
        print "Function name::" + self.fnc_name
        self.inst_cnt = self.json_obj[0]["size"] / 4
        #print "inst_cnt for " + self.fnc_name + "::" + str (self.inst_cnt)

    def seek_zircon(self, block_addr, inst_in_block):
        cnt = 0
        found = False
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

    def view_addresses (self):
        #print '\n\nDisplaying all from/to addreses generated for each block in input json file'
        print "Starting block has address:" + self.source_block_address
        print "Terminal block has address:" + str (self.term_blocks_addr)
        #for addr in self.addr_list:
        #    print str(addr)

    def show_linear_fn(self):
        print "\nAll linear terminal functions are:"
        total_cnt = 0
        for fn, cnt in self.linear_fn.iteritems():
            print fn
            total_cnt += cnt
        print total_cnt

    def show_looping_fn(self):
        print "\nAll looping terminal functions are:"
        for fn in self.looping_fn:
            print fn

    def get_incoming_nodes(self, curr):
        incoming_nodes = []
        for every_tuple in self.addr_list:
            if every_tuple[1] == curr:
                incoming_nodes.append (every_tuple[0])
        return incoming_nodes

    # wrapper method for the recursive method generate_paths()
    def generate_paths_wrapper(self):
        print "Generating all possible path form source to destination...\n"
        for each_term_block in self.term_blocks_addr:
            self.generate_paths(self.source_block_address ,each_term_block, each_term_block)

    def discover_loops_wrapper(self):
        ancestor_nodes = []
        for each_terminal in self.term_blocks_addr:
            self.discover_loops(each_terminal, each_terminal, ancestor_nodes)
        if self.loop_counter == 0:
            print "No loops found in function:" + self.fnc_name
            self.linear_fn[self.fnc_name] = self.inst_cnt
            self.generate_paths_wrapper()
            self.generate_main()
        else:
            print "Total loops found:" + str(self.loop_counter)
            self.looping_fn.append(self.fnc_name + "::" + str(self.loop_counter) + "\tSimple loops::" + str(self.simple_loop_counter) + "\tComplex loops::" + str(self.complex_loop_counter))



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

    def show_all_block_addresses(self):
        print "All block addresses in the CFG from source block to destination block are:"
        for block in self.all_block_addresses:
                print str(block) + "\n"

    #def show_paths(self):
        #f=open("zircon_verified_terminals_paths.txt", "a")
        #f.write("\n" + self.fnc_name + "\t")
        #for path in self.all_possible_paths:
        #        print str(path) + "\n"
        #        f.write(str(path) + "\t")
        #f.close()

    def generate_main(self):
        self.main_file = self.fnc_name + "_main"
        self.main_file_ptr = open(self.output_pvs_files + self.main_file.upper()  +".pvs" , "w")
        self.main_file_ptr.write(self.fnc_name.upper()+ "_MAIN" +" [ ( IMPORTING arm_state ) p : s ] : THEORY" +"\n" )
        self.main_file_ptr.write ("\n    BEGIN\n")
        self.main_file_ptr.write ("\n      IMPORTING")
        f=open("stats.log","a+")
        f.write(self.fnc_name + "\n")
        f.write(str(len(self.all_block_addresses)) + "," + str(len(self.all_possible_paths)) + "\n" )
        f.close()
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
        # patch main_file_issue
        if len (self.all_possible_paths) > 1:
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
                                self.main_file_ptr.write ( tabs + self.fnc_name.upper() + "_" + each_node.upper()+ "[ p ]" + "\n\t\t\t")
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
        #patch main_file_issue to change the output of main.pvs because of pvs7 bug 05/01/2019 
        else:
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
                                self.main_file_ptr.write ( tabs + self.fnc_name.upper() + "_" + each_node.upper()+ "[ p ]" + ".B_post" + "\n\t\t\t")
                                #print ( "C_0::" + str(index) + "::\t" + tabs + self.fnc_name.upper() + "_" + each_node.upper()+ "[ p ]" + ".B_post" + "\n\t\t\t")
                            else:
                                self.main_file_ptr.write ( tabs + self.fnc_name.upper() + "_" + each_node.upper() + ".B_post]" + "\n\t\t\t")
                                #print ( "C_2::" + str(index) + "::\t" + tabs + self.fnc_name.upper() + "_" + each_node.upper() + ".B_post]" + "\n\t\t\t")
                        else:
                            self.main_file_ptr.write ( tabs + self.fnc_name.upper() + "_" + each_node.upper() + "[" + "\n\t\t\t")
                            #print ( "C_1::" + str(index) + "::\t" +  tabs + self.fnc_name.upper() + "_" + each_node.upper() + "[" + "\n\t\t\t")
                    self.main_file_ptr.write (  "\t    " )
                    #for index, each_node in enumerate(path):
                    #    if index == len(path) -1:
                    #        self.main_file_ptr.write (  ".B_post" )
                    #    else:
                    #self.main_file_ptr.write (  ".B_post]" )
                    self.main_file_ptr.write ("\n\n")
                    idx+=1
        self.main_file_ptr.write ("\n    END " + self.main_file.upper() + "\n")

    def pretty_print_json(self):
         print json.dumps( self.json_obj, sort_keys=True, indent=4)

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
            output_file = open(self.current_path + self.output_dir + output_file_name , "w")
            block_ops  =  block["ops"]
            for item in block_ops:
                #patch b_uncond to add control flow information to .dec files for use by auto_decoder.py
                jump=""
                fail =""
                if "jump" in item:
                    jump = str(item["jump"])
                if "fail" in item:
                    fail = str(item ["fail"])
                output_file.write (str(item["offset"]) + "\t" + str(item["bytes"]) + "\t" + "j_" +jump + "\t" + "f_" + fail + "\t" + str(item ["opcode"]) + "\n")

                
                # write the fields from json to the .dec block file

cfg_fp = cfg_json_parser()
cfg_fp.show_linear_fn()
cfg_fp.show_looping_fn()
#cfg_fp.generate_paths_wrapper()
#cfg_fp.show_paths()
#cfg_fp.show_all_block_addresses()
#cfg_fp.generate_main()
#cfg_fp.pretty_print_json()
