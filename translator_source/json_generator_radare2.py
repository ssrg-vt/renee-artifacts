import r2pipe
import re
import os
import sys
import json
import time
class json_generator:

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
        self.current_path = os.getcwd() + "/"
        print "Loaded file for analysis"
        self.input_dir = "assets/intermediate_term_files/"
        self.output_dir = "assets/intermediate_json_files/"
        self.input_file = sys.argv[1]
        self.output_batch_file = self.input_file.replace(".term", ".batch")

    def pretty_print_json(self):
         print json.dumps( self.json_obj, sort_keys=True, indent=4)

    def generate_input_json_file(self):
        input_ptr = open (self.current_path + self.input_dir + self.input_file, "r")
        output_batch_ptr = open (self.current_path + self.output_dir + self.output_batch_file, "w")
        print "Generating json files for terminal functions at " +  self.output_dir + "...\n"
        time.sleep(0.1)
        for line in input_ptr:
            line = line.strip()
            fnc_to_analyze = line
            output_file = fnc_to_analyze + ".json"
            fnc_callgraph_json = (self.r2.cmdj("agfj @" + fnc_to_analyze))
            output_file_ptr = open (self.current_path + self.output_dir + output_file, "w")
            output_file_ptr.write(json.dumps ( fnc_callgraph_json,sort_keys=True, indent=4))
            print "Generating json file:" + output_file 
            output_batch_ptr.write (output_file + "\n")

j=json_generator()
j.generate_input_json_file()
