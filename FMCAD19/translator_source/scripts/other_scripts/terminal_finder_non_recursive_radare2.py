'''
This is an alternative uimplementation of the terminal function finder. It does not use a recursive algorithm but instead used agc on every fnc of the zircon.elf to find terminal fnc

Input file format
0xffffffff00001000    1 108          sym.park_cpu_thread_void
0xffffffff00001070    5 22240 -> 100  sym.platform_init_postvm_unsignedint
0xffffffff00001080    3 140          sym.save_mexec_zbi_zbi_header_t


# In order to generate this file for an ARM 64 binary, open terminal 
# r2 <binary_name>
# radare2 terminal, type
# aa
# afl > all_functions_<binary_name>.txt
# This will generate the required file which will be the input file for this script.Running this script will create a # text file with all the terminal functions from that binary.
# Run the script using
# python terminal_finder_non_recursive_radare2.py > all_linux_terminals.txt
'''


import r2pipe
import re

class terminal_fnc_finder_alt:

    def __init__(self):
        self.r2 = r2pipe.open("zircon.elf")
        self.r2.cmd('aa')
        print ("Loaded file for analysis")
        self.input_file = "all_zircon_functions.txt"
        self.accept = []
        self.reject = []
        #print self.fnc_callgraph_json

    def find_functions_to_panic(self):
        print("Finding functions that call _panic")
        input_ptr = open (self.input_file, "r")
        cnt = 0
        imports = None
        for line in input_ptr:
            line = line.strip()
            tokens = re.split("\s+", line)
            if len (tokens) > 2:
                if 'sym.' in tokens[3]:                  
                    fnc_to_analyze = tokens[3]
                    fnc_callgraph_json = (self.r2.cmdj("agcj @" + fnc_to_analyze))
                    if len (fnc_callgraph_json) > 0:                       
                        if "imports" in fnc_callgraph_json[0] and (len (fnc_callgraph_json[0]["imports"])) > 0:
                            imports = fnc_callgraph_json[0]["imports"]
                            if imports and "sym._panic" in imports:
                                cnt+=1
                                if len(imports) == 1:
                                    print (fnc_to_analyze)
    
                    #if len(imports) > 0:
                    #    for item in imports:
                    #       print item                           
        #print "Total count of functions calling panic:" + str(cnt)

    def find_terminal_fnc(self):
        input_ptr = open (self.input_file, "r")
        cnt = 0
        for line in input_ptr:
            line = line.strip()
            tokens = re.split("\s+", line)
            if len (tokens) > 2:
                if 'sym.' in tokens[3]:
                    fnc_to_analyze = tokens[3]
                    fnc_callgraph_json = (self.r2.cmdj("agcj @" + fnc_to_analyze))
                    if len (fnc_callgraph_json) == 0:
                        if fnc_to_analyze not in self.accept:
                            self.accept.append (fnc_to_analyze)
                            cnt+=1
                    else:
                        if (len (fnc_callgraph_json[0]["imports"])) == 0:
                            if fnc_to_analyze not in self.accept:
                                self.accept.append(fnc_to_analyze)
                                cnt+=1
                        else:
                            self.reject.append(fnc_to_analyze + "::" + str(len(fnc_callgraph_json)) )
        print "Total count:" + str(cnt)

    def print_accept(self):
        for item in self.accept:
            print item



t = terminal_fnc_finder_alt()
#t.find_terminal_fnc()
#t.print_accept()
t.find_functions_to_panic()
