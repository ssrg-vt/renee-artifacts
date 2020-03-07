# This script is used to write the json output of the basic blocks for a terminal fnc using the radare2 cmd afbj
# Usage python analyze_terminals.py
# required files in supporting folder => zircon.elf and
# Sample input file format  *.term

'''


'''

import r2pipe
import sys

class analyze_terminals:
  def __init__(self):
      self.r2 = r2pipe.open("zircon.elf")
      self.r2.cmd('aa')
      self.input_file_ptr = open ("total_terminal_fn_from_syscalls_aggregated.txt")
      self.output_file = "analysis_terminals" + ".txt"
      self.file_ptr = open (self.output_file, "w+")
      self.debug_flag = False

      # Function calls
      self.read_file()

  def read_file(self):
     for fn in self.input_file_ptr:
         fnc_to_analyze = fn.strip()
         fnc_callgraph_json = (self.r2.cmdj("afbj @" + fnc_to_analyze))
         if len (fnc_callgraph_json) > 0:
             #print str (fnc_callgraph_json) +"\n"
             self.file_ptr.write("\nanalysis for function:"  + fn)
             self.file_ptr.write(str (fnc_callgraph_json) + "\n")

analysis_1 =  analyze_terminals()
