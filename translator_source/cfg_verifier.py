# This script is used for validation of auto-decoder output. The starting point is a batch file with the file names of pvs files to be validated. It compares the instructions in the output pvs files and matches their bytecode with their name. It is a rveerse lookup

import xml.etree.ElementTree as ET
import sys
import json
import re
import collections
import time
import os


class cfg_verifier:

    def __init__(self):
        self.current_path = os.getcwd().strip() +"/"
        self.input_files_dir_path = "/output_pvs_files/"
        self.input_batch_file_dir = "assets/misc/"
        self.input_batch_file = "linux_verified_mains.txt"
        self.mismatch = False
        self.batch_ptr = open (self.current_path+ self.input_batch_file_dir + self.input_batch_file, "r")
        for line in self.batch_ptr:
            self.all_paths_dir = "/assets/misc/"
            self.json_paths_file = "linux_verified_terminals_paths.txt"
            self.paths_fileptr = open (self.current_path + self.all_paths_dir + self.json_paths_file,"r")
            line = line.strip()        
            #self.input_filename = "PCISTDCAPABILITY___PCISTDCAPABILITY_MAIN.pvs"
            self.input_filename = line
            self.input_fileptr = open(self.current_path + self.input_files_dir_path + self.input_filename,"r")
            self.json_addrs =[]
            self.pvs_addrs = []
            self.pvs_file_parser()
            self.print_paths_from_json()
            self.paths_fileptr.close()
        if  not self.mismatch:
            print "All files CFG's verified "

    
    def print_paths_from_json(self):

        for line in self.paths_fileptr:
            line = line.strip()
            tokens = re.split("\s+",line)
            
            # Compare the json_paths file fnc names with the output pvs file function name
            if self.input_filename.replace("_MAIN.pvs","").lower() == tokens[0].lower():
                for i in range(len(tokens)):
                    if i == 0:
                        continue
                    else:
                        cleaned_token = tokens[i].replace('[','')
                        cleaned_token = cleaned_token.replace(']','')
                        cleaned_token = cleaned_token.replace(',','')
                        cleaned_token = cleaned_token.replace('"','')
                        cleaned_token = cleaned_token.replace("'",'')
                        if len(cleaned_token) > 8:
                            self.json_addrs.append(cleaned_token)
        if set(self.json_addrs) == set (self.pvs_addrs):
            print "Verified paths in file:" + self.input_filename
        else:
            print "Mismatched for " + self.input_filename
            print self.pvs_addrs
            print self.json_addrs
            self.mismatch = True
       
        

    # Extract the address from the pvs file based on the b_post and put each path as a list
    def pvs_file_parser(self):
        file_list = []
        l=[]
        l2 = []
        flag = False
        for line in self.input_fileptr: 
            line = line.strip()
            file_list.append(line)
        for i in file_list:
            if "_post" in i:
                flag = True
            if "B_post" in i and flag:
                l2.append(l)
                l=[]
                flag = False 
            if flag:
                #print i
                l.append(i)
        for j in l2:
            for k in j:
                self.pvs_addrs.append((k.rsplit("_",1)[1][0:16]).lower())
        #print self.pvs_addrs

    def extract_block_names(self, file_list):
        l =[]
        for i in file_list:
            if "IMPORTING" in i and "THEORY" not in i:
                flag = True
            if len(i) == 0 and flag:
                print ""
                break 
            if flag:
                print i
                l.append(i)



start_time = time.time()
cfg = cfg_verifier()
print("--- %s seconds ---" % (time.time() - start_time))

