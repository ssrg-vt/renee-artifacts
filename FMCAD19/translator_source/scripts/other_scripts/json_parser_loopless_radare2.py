# usage: python cfg_json_parser.py test_output.json => test_output.json is the json file generated for a function from radare2 using the command agfj <fn_name>
# required files zircon.assembly , >input_json_file_from_radare>


import sys
import json
import re
import collections
import os

class cfg_json_parser:

    def __init__(self):
         self.cfg_file = sys.argv[1]                        #json file
         self.cfg_file_ptr = open(self.cfg_file,"r")        #json_file_ptr
         self.json_obj = json.load(self.cfg_file_ptr)
         self.target_binary_file = "zircorn.assembly"
         self.target_binary_file_ptr = None
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

         # fnc calls from init
         self.parse_file()

    def tohex(self, val, nbits):
        return hex((val + (1 << nbits)) % (1 << nbits))

    def parse_file (self):
        self.extract_fnc_name()
        self.extract_blocks()

    def extract_fnc_name(self):
        self.fnc_name = str (self.json_obj[0]["name"])[4:]
        print self.fnc_name

    # This function is called by the extract blocks
    def seek_zircon(self, block_addr, inst_in_block):
        cnt = 0
        found = False
        self.target_binary_file_ptr = open(self.target_binary_file, "r")
        output_dir = "output_path_loop_finder/"
        output_file_name = self.fnc_name +"_" + block_addr + ".txt"
        output_file = open(output_dir + output_file_name , "w")
        print 'searching for block address in zircon file...' + str(block_addr)
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
        print "Finished parsing generating file:" + output_file_name + "in dir " + output_dir

    def view_addresses (self):
        print '\n\nDisplaying all from/to addreses generated for each block in input json file'
        print "Starting block has address:" + self.source_block_address
        print "Terminal block has address:" + str (self.term_blocks_addr)
        for addr in self.addr_list:
            print str(addr)

    def get_incoming_nodes(self, curr):
        incoming_nodes = []
        for every_tuple in self.addr_list:
            if every_tuple[1] == curr:
                incoming_nodes.append (every_tuple[0])
        return incoming_nodes

    # wrapper method for the recursive method generate_paths()
    def generate_paths_wrapper(self):
        print "\nGenerating all possible path form source to destination...\n"
        for each_term_block in self.term_blocks_addr:
            self.generate_paths(self.source_block_address ,each_term_block, each_term_block)

    def discover_loops_wrapper(self):
        ancestor_nodes = []
        for each_terminal in self.term_blocks_addr:
            self.discover_loops(each_terminal, each_terminal, ancestor_nodes)
        if self.loop_counter == 0:
            print "No loops found\n"
        else:
            print "Total loops found:" + str(self.loop_counter)



    def discover_loops(self, term, curr, ancestor_nodes):
        nodes_to_visit = self.get_incoming_nodes(curr)
        remove_list = []
        next_node = None
        # This condition checks for the loops from the current node
        for node in nodes_to_visit:
            # if any node in the list of nodes to visit is already in the stack of ancestor nodes then this is a loop because of the presence of a backedge
            if node in ancestor_nodes or node == curr:
                print "loop discovered"
                self.loop_counter += 1
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

    def show_paths(self):
        print "All paths in the CFG from source block to destination block are:"
        for path in self.all_possible_paths:
                print str(path) + "\n"

    def generate_main(self):
        self.main_file = self.fnc_name + "_main"
        self.main_file_ptr = open(self.main_file.upper()  +".pvs" , "w")
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

    def pretty_print_json(self):
         print json.dumps( self.json_obj, sort_keys=True, indent=4)

    def extract_blocks(self):
        blocks =  (self.json_obj[0]["blocks"])
        start_address = (self.json_obj[0]["offset"])
        for block in blocks:
            print  "\n****** Found a new block ******"
            block_addr_curr = None
            inst_in_block = None
            if "offset" in block:
                #print "offset:" + str(self.tohex(int (block["offset"]), 64)[:-1])[2:]
                block_addr_curr = str(self.tohex(int (block["offset"]), 64)[:-1])[2:]
                self.all_block_addresses.append (block_addr_curr)
            if start_address == block["offset"]:
                print "Starting block address recorded"
                self.source_block_address =  block_addr_curr
            if "jump" in block:
                #print "jump:" + str (self.tohex(int (block["jump"]), 64)[:-1])[2:]
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
                #print "fail" + str (self.tohex(int (block["fail"]), 64)[:-1])[2:]
                block_addr_false = str (self.tohex(int (block["fail"]), 64)[:-1])[2:]
                temp2 = (block_addr_curr, block_addr_false , "f")
                self.all_block_addr_symbols.append (block_addr_true + "_f")
                self.addr_list.append(temp2)
            if not "jump" in block and  not "fail" in block:
                self.term_blocks.append(block)
                self.term_blocks_addr.append(block_addr_curr)
            inst_in_block = block['size']/4
            print "\nnos of instructions in current block:" +  str(block['size']/4)
            self.seek_zircon(block_addr_curr, inst_in_block )

cfg_fp = cfg_json_parser()
cfg_fp.view_addresses()
cfg_fp.discover_loops_wrapper()
#cfg_fp.generate_paths_wrapper()
#cfg_fp.show_paths()
#cfg_fp.show_all_block_addresses()
#cfg_fp.generate_main()
#cfg_fp.pretty_print_json()
