#!/usr/bin/env python
import xml.etree.ElementTree as ET
import sys
import json
import re
import os
import os.path as path
import pickle


class pvs_lemma_generator:
	
	def __init__(self):
		self.inst_name = sys.argv[1].upper()		
		self.f = open ("TEST_" + self.inst_name + ".pvs" , "w")
		self.inst_name = ""
		self.ip1_val = ""
		self.ip2_val = ""
		self.R_ip1 = ""
		self.R_ip2 = ""
		self.R_NZCV = ""
		self.R_PC = ""
		self.input_bitstring = ""
		self.input_init_addr = ""
		self.input_final_addr = ""
		self.output_reg = ""	
		

	def parse_unicorn_output_file(self):	
		self.R_ip1_val = "bv(0b0100000000000000000000000000000000000000000000000000000000000000)"
		self.R_ip2_val = "bv(0b0000000000000000000000000000000000000000000000000000000000000000)"
		self.R_ip1 = "2"
		self.R_ip2 = "5"
		self.R_op = self.R_ip1
		self.R_NZCV = "bv( 0b0000 )"
		self.R_PC = "65536"
		self.input_bitstring = "bv(0b01000010000000001010000011010111)"
		self.input_init_addr = "65536"
		self.output_reg = "bv(0b0100000000000000000000000000000000000000000000000000000000000000)"                 

	def generate_pvs_lemma_file(self):
		self.inst_name = "SUBS_ADDSUD_SHIFT"		
		self.f.write ("test_".upper() + self.inst_name )
		self.f.write ("      : THEORY")
		self.f.write ("\n      BEGIN")
		self.f.write ("\n      IMPORTING arm_state")
		self.f.write ( "\n      X_sts : [ below(32) -> bvec[64] ]  = init`X  with [("+self.R_ip1+"):=" +  self.ip1_val + "," + "\n\t\t\t\t\t\t\t ("+self.R_ip2 +"):=" + self.R_ip2 + "]\n")		                                         
		self.f.write ( "\n      p1    :  s = init with [`X:= X_sts, `NZVC:=" +self.R_NZCV  + "," "`PC:=" +  self.R_PC +   "]")  
		self.f.write ( "\n      importing concrete_test_subsaddsubshift[p1]{{Diag:=" + self.input_bitstring +", addr:=" + self.input_init_addr + "}}\n")        
		self.f.write ( "\n      test1: lemma let X_post =  p1`X with [ (2):=" + self.output_reg + "] in\n")
		self.f.write ( "\n          let p2     =  p1 with [`X:= X_post, `NZVC:= bv( 0b0010) , `PC:= 65540  ] in\n")   
		self.f.write ( "\n          concrete_test_subsaddsubshift[p1].post`X(2) = p2`X(2)\n")
		self.f.write ("\n%|- test1 : PROOF  (test-subs-addsub-shift" + self.R_op +")  ")
		self.f.write ("\n%|- QED")
		self.f.write ( "\nEND test_".upper() + self.inst_name)

if __name__ == '__main__':
	pg = pvs_lemma_generator()
	pg.parse_unicorn_output_file()
	pg.generate_pvs_lemma_file()
	print "Generating TEST_SUBS_ADDSUB_SHIFT.pvs"
