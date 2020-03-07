# usage: python json_parser_analysis_script.py test_output.batch => It will print the output to the console
# 1 bug / issues !> Stats are not generated for the main files for each function

import sys
import json
import re
import collections
import os
import csv
 


class cfg_json_parser:

    def __init__(self):
    	 self.current_path = os.getcwd()
    	 self.input_dir = self.current_path + "/intermediate_json_files/"
    	 self.output_dir = "intermediate_dec_files/"
         self.batch_file = sys.argv[1]                          		 #input batch file with .json filenames
         self.batch_file_ptr = open(self.input_dir + self.batch_file,"r")        #json_file_ptr for batch input file
         self.output_batch_file_name = self.batch_file + "_dec"
    	 self.output_batch_file_ptr = open ( self.output_dir + self.output_batch_file_name , "w")
         self.target_binary_file = "zircorn.assembly"
         self.target_binary_file_ptr = None
         self.results_file = None
         self.output_pvs_files = "output_pvs_files/"
         self.total_inst = 0
	 self.stats = []
	 self.stats_cyclic = []
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
	 self.output_batch_file_ptr.close() 

    def tohex(self, val, nbits):
        return hex((val + (1 << nbits)) % (1 << nbits))
    
    def generate_stats_csv(self):
	with open("stats_" + self.batch_file.replace(".batch_dec", "") + ".csv", 'a') as outcsv:   
    		#configure writer to write standard csv file
    		writer = csv.writer(outcsv, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL, lineterminator='\n')
    		writer.writerow(['fn_name', 'assembly', 'pvs_blocks', 'pvs_main'])
                sum_asm = 0
                sum_pvs_blocks = 0
                sum_pvs_main = 0
		for item in self.stats:
		    if item[4] == False:
			 sum_asm+= int(item[1])
			 sum_pvs_blocks+= int(item[2])
			 sum_pvs_main+= int(item[3])	
                         writer.writerow([item[0], item[1], item[2], item[3]])
		writer.writerow(["total", str(sum_asm), str(sum_pvs_blocks), str(sum_pvs_main)])

    
    # helper method to provide the line count of a given file without blank lines in the output pvs files directory
    def cnt_lines_in_file(self, fname):
	try:	
		f = open (self.output_pvs_files + fname , "r")
	except IOError as e:
    		print("Couldn't open or write to file (%s)." % e)
		return 0
	cnt = 0
	for line in f:
		if line.strip():
             		cnt+=1
	return cnt

    # generates stats for total nos of insts for the toolchain output
    def generate_pvs_stats(self):
	batch_file = "intermediate_dec_files/" + self.batch_file.replace (".batch", ".batch_dec")
	batch_file_ptr = open (batch_file,"r")
	print "file opened successfully:" + batch_file	
	fnc_name_curr = ""
	fnc_name_prev = ""
	total_lines_fn = 0
	for line in batch_file_ptr:
		# read line from file and add the appropriate extensions
		line  = line.strip()
		
		fname = line.replace(".dec", "").upper()
		# handle the case where :: and __ are replaced by __ and F_ while creating pvs files to avoid naming issues
		if fname.startswith("__"):
			fname.replace("__", "F__", 1)
	        fname = fname.replace("::","__") + ".pvs"			
		num_lines = self.cnt_lines_in_file (fname)
		fnc_name_curr = line.rsplit("_", 1)[0]
		# New fn name found
		if fnc_name_prev <> fnc_name_curr: 			
			if fnc_name_prev <> "":
				# After all the basic block loc have been counter, count the main file and add it to the total
				main_file_name = fnc_name_prev
				if main_file_name.startswith("__"):
					main_file_name.replace("__", "F__", 1)
	        		main_file_name = main_file_name.replace("::","__")
				main_file_name = main_file_name.upper() + "_MAIN.pvs"
				main_file_lines = self.cnt_lines_in_file (main_file_name)					
				print "Nos of lines in " + fnc_name_prev + "::" + str (total_lines_fn)
				# loop over the stats list which has the info about the aseembly lines of code fnc name and 
				#add the pvs lines of code to it list with the pvs lines of code info				
				for fn_stats in self.stats:
					if fnc_name_prev in fn_stats: 	# find the list inside the list which has data for the given fn
						fn_stats.append(str(total_lines_fn))
						fn_stats.append(str(main_file_lines))						
						if main_file_lines == 0:	# cyclic flag is created and set to true for fns whihc have loops
							fn_stats.append(True)
						else:
							fn_stats.append(False)									
				total_lines_fn = 0 			
			fnc_name_prev = fnc_name_curr
		total_lines_fn += num_lines			
	print "Nos of lines in " + fnc_name_prev + "::" + str (total_lines_fn)
	# update the stats tuple with the pvs lines of code info				
	for fn_stats in self.stats:
		if fnc_name_prev in fn_stats:
			fn_stats.append(str(total_lines_fn))
			fn_stats.append(str(main_file_lines))
			if main_file_lines == 0:	# cyclic flag is created and set to true for fns whihc have loops
				fn_stats.append(True)
			else:
				fn_stats.append(False)

    



    def extract_fnc_name(self):
        self.fnc_name = str (self.json_obj[0]["name"])[4:]
	self.inst_cnt = self.json_obj[0]["size"] / 4
        print "Terminal fnc:" + self.fnc_name + "\t" + str (self.inst_cnt) + "\n"
	fn_stats = [self.fnc_name , str(self.inst_cnt) ]
	self.stats.append (fn_stats)



    def view_addresses (self):
        print '\n\nDisplaying all from/to addreses generated for each block in input json file'
        print "Starting block has address:" + self.source_block_address
        print "Terminal block has address:" + str (self.term_blocks_addr)
        for addr in self.addr_list:
            print str(addr)


    def pretty_print_json(self):
         print json.dumps( self.json_obj, sort_keys=True, indent=4)



cfg_fp = cfg_json_parser()
cfg_fp.extract_fnc_name()
cfg_fp.extract_blocks()
cfg_fp.generate_pvs_stats()
cfg_fp.generate_stats_csv()
#cfg_fp.show_linear_fn()
#cfg_fp.show_looping_fn()
#cfg_fp.generate_paths_wrapper()
#cfg_fp.show_paths()
#cfg_fp.show_all_block_addresses()
#cfg_fp.generate_main()
#cfg_fp.pretty_print_json()
