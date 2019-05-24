#usage python terminal_fnc_finder.py file1.r2
# Required files zircon.elf (for loading in radare2) and zircon_syscall_fn.txt (for finding terminals for each syscall)
# Sample inputs from the zircon_syscall_fn.txt
'''
Input file sample

sym.sys_clock_get_unsignedint
sym.sys_socket_write_unsignedint_unsignedint_internal::user_ptr_voidconst__internal::InOutPolicy_1__unsignedlong_internal::user_ptr_unsignedlong__internal::InOutPolicy_2
sym.sys_job_set_policy_unsignedint_unsignedint_unsignedint_internal::user_ptr_voidconst__internal::InOutPolicy_1__unsignedint
sym.sys_object_signal_unsignedint_unsignedint_unsignedint

'''
import r2pipe
import sys
import os

class terminal_fnc_finder:
    counter = 0

    def __init__(self):
        self.current_path = os.getcwd().strip() +"/"
        self.ARM_binaries_dir = "/assets/ARM_binaries/"
        if sys.argv[2] == "--linux":
            self.binary_input_file = "vmlinux"
        elif sys.argv[2] == "--zircon":
            self.binary_input_file = "zircon.elf"
        else:
             self.binary_input_file = "zircon.elf"
        self.r2 = r2pipe.open(self.current_path + self.ARM_binaries_dir + self.binary_input_file)
        self.r2.cmd('aa')
        self.current_path = os.getcwd() 
        self.input_file = sys.argv[1]
        self.input_dir = "/assets/input_r2_files/"
        self.input_file_ptr = open (self.current_path + self.input_dir  + self.input_file, "r")
        self.visited_set = []
        self.terminal_fnc = []
        self.max_depth = 10          # does not matter will be fixed in next release
        self.call_stack = ""
        self.call_stack_list = []
        self.all_terminas = []
        self.output_file = self.input_file.replace (".r2" , ".term")
        self.output_file_fn = self.input_file.replace (".r2" , ".fn_term")
        self.output_dir = "/assets/intermediate_term_files/"
        self.file_ptr = open  ( self.current_path + self.output_dir + self.output_file, "w+")
        self.fnc_to_analyze = ""
        self.debug_flag = False

        # Function calls
        self.read_file()


    def read_file(self):
        for fn in self.input_file_ptr:
            #print "Loaded file for analysis\n"
            self.terminal_fnc[:] = []
            self.visited_set [:] = []
            self.fnc_to_analyze = fn.strip()
            if self.fnc_to_analyze == "sym.sys_object_signal_unsignedint_unsignedint_unsignedint":
                print "Debug flag set"
                self.debug_flag = True
            self.fnc_callgraph_json = (self.r2.cmdj("agcj @" + self.fnc_to_analyze))
            #print str (self.fnc_callgraph_json)
            if len (self.fnc_callgraph_json) > 0:
                self.find_terminal_fnc_wrapper()
                self.print_terminal_fn()


    def get_counter(cls):
        terminal_fnc_finder.counter +=1
        return terminal_fnc_finder.counter

    def find_terminal_fnc_wrapper(self):
        print "Analyzing function callgraph for " + self.fnc_to_analyze
        if "imports" in self.fnc_callgraph_json[0]:
            calling_fn_list = self.fnc_callgraph_json[0]["imports"]
            #print str (calling_fn_list)
            for each_fn in calling_fn_list:
                self.find_terminal_fnc(each_fn,each_fn)

    def print_terminal_fn(self):
        file_ptr = open (self.current_path + self.output_dir + self.output_file_fn , "a+")
        cnt = 0
        '''
        if self.debug_flag == True:
            print "prinitng for " + self.fnc_to_analyze
            print str(self.terminal_fnc) +"\n"
        '''
        file_ptr.write( "\nTerminal fnc list for " +  self.fnc_to_analyze +  "\n")
        for fn in self.terminal_fnc:
            cnt+= 1
            if fn not in self.all_terminas:
                self.all_terminas.append(fn)
            file_ptr.write(fn + "\n")
            #print "fn:" + fn + " written to the file \n"
        print "Total count:" + str(cnt) + "\n"
        file_ptr.write("Total count:" + str(cnt) + "\n")

    def print_all_terminals(self):
        file_ptr = open (self.current_path + self.output_dir + self.output_file, "w")
        cnt = 0
        for fn in self.all_terminas:
                file_ptr.write(fn + "\n")
        #file_ptr.write("Total count:" + str(cnt))


    def find_terminal_fnc(self, curr_fn, call_stack):
        '''
        if self.debug_flag == True:
            print "Current fn is:" + curr_fn
        '''
        call_stack = call_stack + "::" + curr_fn
        self.visited_set.append(curr_fn)
        i = self.get_counter()
        #print "Counter called:" + str(i)
        if  i == self.max_depth:
        #    print "******max depth reached*******"
            return
        else:
            curr_fnc_callgraph_json = (self.r2.cmdj("agcj @" + curr_fn))
            curr_calling_fn_list = list (curr_fnc_callgraph_json[0]["imports"])
            '''
            if self.debug_flag == True:
                print str(curr_calling_fn_list)
            '''

            if len(curr_calling_fn_list) == 0:
                print curr_fn[0:10] + "::" + str(curr_calling_fn_list)
                if curr_fn not in self.terminal_fnc:
                    #print "added:" + curr_fn
                    self.terminal_fnc.append(curr_fn)
        #        print "Current list is empty"
                return
            else:
        #        print "call graph for fnc " + curr_fn + ":" + str (curr_calling_fn_list)
                for each_fn in curr_calling_fn_list:
                    if each_fn not in self.visited_set:
                        self.call_stack = each_fn
                        #print "rec call for " + curr_fn +"\n"
                        self.find_terminal_fnc(each_fn, self.call_stack)
        # print(r2.cmdj("aflj")) # evaluates JSONs and returns an object
        # starting point  = some function
        # list of imports = agcj for the current func
        # set_terminal_fnc
        # set_visited => after every function has been visited
tff =  terminal_fnc_finder()
tff.print_all_terminals()
#tff.call_stack_list()
