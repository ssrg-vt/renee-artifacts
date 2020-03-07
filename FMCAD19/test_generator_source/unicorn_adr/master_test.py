
#!/usr/bin/env python
# This file is used to generate a random instruction and pass the random bittring to unicorn emulator which generates the output with the inst name and the hex string which can be parsed by pther scripts to generate pvs code

from __future__ import print_function
from unicorn import *
from unicorn.arm64_const import *
import xml.etree.ElementTree as ET
import sys
import json
import re
import os
import os.path as path
import random

ADDRESS = 0x10000

class inst_generator:
    def __init__(self, inst_filename):

        self.curr_dir_path = os.path.abspath(os.curdir)
        self.parent_dir_path = path.abspath(path.join(__file__, "../.."))
        self.inst_length = None
        self.output_file = ""
        self.fields = []
        self.Rd = ""
        # self.Rn = ""
        # self.Rm = ""

        # This is the specific instruction file which needs to be translated
        self.inst_file_name = inst_filename
        print ("Generating random bitstring for the instruction::" +
               self.inst_file_name.replace(".xml", ""))
        self.inst_tree = ET.parse(
            self.parent_dir_path + "/" + self.inst_file_name)
        self.inst_root = self.inst_tree.getroot()
        self.inst_bitstring = ""
        # stores an int_list bytestring version of the randomly generated 32 bit bitstring whihc is input to unicorn
        self.bytestr = None
        self.hexstring = ""
        self.hexstring_list = []	       # This stores it in the regular hexadecimal form
        # This one stores the hexstrings in the form which is the input for unicorn
        self.hexstring_pickle_list = []

    # For testing xmlTree
    def display_inst_root(self):
        print (self.inst_root.attrib)

    # Emptys the class variables
    def flushall(self):
        self.inst_bitstring = ""
        self.hexstring = ""

    # returns the reversed bitstring which is the bitstring format in PVS
    def get_pvs_bitstring(self):
        return self.inst_bitstring[::-1]

    # generate an output file that has the randomly generated hex code for unicorn and the printed output file for pvs for an instruction

    def generate_validation_file(self):
        # self.file_ptr = open(cur_dir +"/" + self.output_file,"w")
        self.flushall()
        self.generate_binary_inst()

    # returns the hexstring of the random bitstring
    def get_hexstring(self):
        return self.hexstring[2:]

    # auto generates a random bitstring and hexstring for the input instruction
    def generate_binary_inst(self):
        for field in self.fields:
            substr = ""
            f_name = ""
            # 64 bit inst only
            if 'name' in field and field['name'] == "sf":
                substr = "1"
            else:
                if "bitvector" in field and field['bitvector'] != "":
                    substr = field['bitvector']
                elif "width" in field:
                    str_len = int(field["width"])
                    substr = self.generate_random_bitstring(str_len)
            if 'name' in field:
                f_name = field['name']
                # set values of Rd, Rn, Rm
                if f_name == "Rm":
                    self.Rm = int(substr, 2)
                if f_name == "Rd":
                    self.Rd = int(substr, 2)
                if f_name == "Rn":
                    self.Rn = int(substr, 2)
                # comment works only for negative tests for now a flag will be setup to take care of psitive
                if f_name == "shift":
                    if substr == "11" or substr == "10":
                        substr = ["01", "00"][random.randint(0, 1)]

            else:
                f_name = "fixed_bitvector"
            print (f_name + " (reveresed for PVS) = " + substr[::-1])
            self.inst_bitstring += substr

        self.hexstring = str(hex(int(self.inst_bitstring, 2)))
        self.hexstring_list.append(self.hexstring)
        print ("Bitstring (reversed for PVS) = " + self.inst_bitstring[::-1])
        print ("Hexstring = " + self.hexstring)
        self.create_bytes_array()

    # return the bytestring for the instruction
    def get_bytestr(self):
        return self.bytestr[::-1]
        # return b'\xf6\x0a\x0b\xeb'

    # return the register values from the inst
    def get_registers(self):
        reg_list = [str(self.Rd)]
        return reg_list

    # view all the regdiagram fields for an instruction
    def view_fields(self):
        for x in self.fields:
            print (x)

    # fields is a dictionary that keeps track of each field in the xml. the xml tag has the name 'box'. Each field is added to the list self.fields
    def extract_fields(self):
        for node in self.inst_root.findall(".//regdiagram"):
            self.inst_length = node.attrib['form']
            for box in node:
                field = {}
                bvec = ''
                field.update(box.attrib)
                for c in box:
                    if c.text is not None:
                        bvec += c.text
                field['bitvector'] = bvec
                self.fields.append(field)

    # generates a random bitsrting of length str_len
    def generate_random_bitstring(self, str_len):
        bitstring = ""
        for i in range(str_len):
            bitstring += str(random.randint(0, 1))
        # Do not let the randomizer generate a string of binary value 31 as there is no X31 register in Unicorn
        if bitstring == "11111":
            bitstring = "11101"
        return bitstring

    # creates a byte array from the 32 bit bitstring of the form b"\xff\xff\xff\xff"

    def create_bytes_array(self):
        int_list = []
        # chop the bitsring into 8 bits at a time convert to int and add to a list
        for i in range(0, 32, 8):
            int_list.append(int((self.inst_bitstring[i:i+8]), 2))
        # convert the list to a bytearray
        self.bytestr = int_list

# memory address where emulation starts


# callback for tracing basic blocks
def hook_block(uc, address, size, user_data):
    return 0
    # print(">>> Tracing basic block at 0x%x, block size = 0x%x" %(address, size))


# callback for tracing instructions
def hook_code(uc, address, size, user_data):
    return 0
    # print(">>> Tracing instruction at 0x%x, instruction size = 0x%x" %(address, size))

# a custom fnc to input a hex string and return the 64 bit bvec in the PVS bvec form (LSB : MSB)


def convert_to_bvec(hex_num, leading_zeros):
    return ("bv(0b" + str(bin(int(hex_num, 16))[2:].zfill(leading_zeros)[::-1]) + ")")

# Test ARM64


def test_arm64(ARM64_CODE, output_file, reg_list):

    # set register values Rd ,  Rn
    Rd = reg_list[0]
    # Rn = reg_list[1]
    # Rm = reg_list[2]

    Rd_val = random.randint(1, 10000000)
    print (Rd_val)
    # Rn_val = random.randint(1, 10000000)
    # print (Rn_val)
    # Rm_val = random.randint(1, 10000000)
    # print (Rm_val)
    # nzcv_val = nzcv_param

    # comment_Amer the number of registers is going to be large. ARM has more thna 800 including general and special purpose
    X_regs = {"0": UC_ARM64_REG_X0, "1": UC_ARM64_REG_X1, "2": UC_ARM64_REG_X2, "3": UC_ARM64_REG_X3, "4": UC_ARM64_REG_X4, "5": UC_ARM64_REG_X5, "6": UC_ARM64_REG_X6, "7": UC_ARM64_REG_X7, "8": UC_ARM64_REG_X8, "9": UC_ARM64_REG_X9, "10": UC_ARM64_REG_X10, "11": UC_ARM64_REG_X11, "12": UC_ARM64_REG_X12, "13": UC_ARM64_REG_X13, "14": UC_ARM64_REG_X14, "15": UC_ARM64_REG_X15,
              "16": UC_ARM64_REG_X16, "17": UC_ARM64_REG_X17, "18": UC_ARM64_REG_X18, "19": UC_ARM64_REG_X19, "20": UC_ARM64_REG_X20, "21": UC_ARM64_REG_X21, "22": UC_ARM64_REG_X22, "23": UC_ARM64_REG_X23, "24": UC_ARM64_REG_X24, "25": UC_ARM64_REG_X25, "26": UC_ARM64_REG_X26, "27": UC_ARM64_REG_X27, "28": UC_ARM64_REG_X28, "29": UC_ARM64_REG_X29, "30": UC_ARM64_REG_X30}

    try:
        print("Emulator output::")
        output_file.write("Rd=" + Rd + "\n")
        # output_file.write("Rn=" + Rn + "\n")
        # output_file.write("Rm=" + Rm + "\n")
        print("Rd=" + Rd)
        # print("Rn=" + Rn)
        # print("Rm=" + Rm)

        # Initialize emulator in ARM mode
        mu = Uc(UC_ARCH_ARM64, UC_MODE_ARM)

        # map 2MB memory for this emulation
        mu.mem_map(ADDRESS, 2 * 1024 * 1024)

        # write machine code to be emulated to memory
        mu.mem_write(ADDRESS, ARM64_CODE)

        # initialize machine registers
        mu.reg_write(X_regs[Rd], Rd_val)
        output_file.write(
            "Rd_pre=bv(0b" + str(bin(Rd_val)[2:].zfill(64)[::-1]) + ")\n")
        # if Rn == Rm:
            # mu.reg_write(X_regs[Rn], Rn_val)
            # output_file.write(
                # "Rn_pre=bv(0b" + str(bin(Rn_val)[2:].zfill(64)[::-1]) + ")\n")
            # change the logic behind the calculation of NZCV flag
            # output_file.write(
                # "Rm_pre=bv(0b" + str(bin(Rn_val)[2:].zfill(64)[::-1]) + ")\n")
            # mu.reg_write(X_regs[Rm], Rn_val)
        # else:
            # mu.reg_write(X_regs[Rn], Rn_val)
            # output_file.write(
                # "Rn_pre=bv(0b" + str(bin(Rn_val)[2:].zfill(64)[::-1]) + ")\n")
            # change the logic behind the calculation of NZCV flag
            # output_file.write(
                # "Rm_pre=bv(0b" + str(bin(Rm_val)[2:].zfill(64)[::-1]) + ")\n")
            # mu.reg_write(X_regs[Rm], Rm_val)

        # output_file.write(
            # "R_NZCV_pre=bv(0b" + str(bin(int(nzcv_val))[2:].zfill(64))[32:36] + ")" + "\n")
        # print(
            # "R_NZCV_pre=bv(0b" + str(bin(int(nzcv_val))[2:].zfill(64))[32:36] + ")")
        print("Rd_pre (without reading from unicorn)=" + convert_to_bvec(str(Rd_val), 64))
        # print("Rn_pre=" + convert_to_bvec(str(Rn_val), 64))
        # mu.reg_write(UC_ARM64_REG_NZCV, nzcv_val)
        # print("Rm_pre=" + convert_to_bvec(str(Rm_val), 64))
        # mu.reg_write(UC_ARM64_REG_NZCV, nzcv_val)
        # mu.reg_write(UC_ARM64_REG_APSR, 0xFFFFFFFF) #All application flags turned on

        # tracing all basic blocks with customized callback
        mu.hook_add(UC_HOOK_BLOCK, hook_block)

        # tracing all instructions with customized callback
        mu.hook_add(UC_HOOK_CODE, hook_code, begin=ADDRESS, end=ADDRESS)
        pc = mu.reg_read(UC_ARM64_REG_PC)
        # Rd_val = mu.reg_read(X_regs[Rd])

        output_file.write("R_PC_pre=65536\n")
        # print ("R_APSR_pre=" + convert_to_bvec( str(apsr), 64)+ ")")
        # emulate machine code in infinite time
        mu.emu_start(ADDRESS, ADDRESS + len(ARM64_CODE))

        # Read values from registers
        Rd_val = mu.reg_read(X_regs[Rd])
        print (str(Rd_val))

        # Rn_val = mu.reg_read(X_regs[Rn])
        # print (str(Rn_val))

        # Rm_val = mu.reg_read(X_regs[Rm])
        # print (str(Rm_val))

        # nzcv_post = mu.reg_read(UC_ARM64_REG_NZCV)
        # print ("post_nzcv_raw::%d" % nzcv_post)
        pc = mu.reg_read(UC_ARM64_REG_PC)
        # Convert the output value of PC to int value for PVS
        pc_int = str(int(str(pc), 16))
        # output values to a file
        output_file.write("Rd_post=bv(0b" + str(bin(Rd_val)[2:].zfill(64)[::-1]) + ")\n")
        # output_file.write("Rn_post=bv(0b" + str(bin(Rn_val)[2:].zfill(64)[::-1]) + ")\n")
        # output_file.write("Rm_post=bv(0b" + str(bin(Rm_val)[2:].zfill(64)[::-1]) + ")\n")
        
        # output_file.write("R_NZCV_post=(0b" + str(bin(int(nzcv_post)).zfill(64)[::-1]) [28:32] + ")" + "\n")
        output_file.write("R_PC_post=65540" + "\n")
        output_file.write("R_op=" + Rd + "\n")
        output_file.write(
            "R_op_val=bv(0b" + str(bin(Rd_val)[2:].zfill(64)[::-1]) + ")" "\n")
        # print("R_NZCV_post=bv(0b" + str(bin(nzcv_post)[2:].zfill(32)[0:4]) + ")" + "\n")
        # output_file.write("R_NZCV_post=bv(0b" + str(bin(nzcv_post)[2:].zfill(32)[0:4]) + ")" + "\n")
        print ("R_op=" + Rd)
        print ("R_op_val=" + str(bin(Rd_val)[2:].zfill(64)[::-1]))
        output_file.close()
    except UcError as e:
        print("ERROR: %s" % e)


'''
if __name__ == '__main__':
	inst_test_suite = inst_generator('')
	# Extracts the diagram format from ASL for each instruction which is provided in the command line as an argument 
	inst_test_suite.extract_fields()
	# Generates a txt file with field names about the random bitstring generated for a particular ARM inst				
	inst_test_suite.generate_validation_file()
        # Extract registers from the previous output
	reg_list = inst_test_suite.get_registers()
        # Fixes the bytestring issue in unicorn for the test genration
	int_list = inst_test_suite.get_bytestr()
	bytecode = bytearray(int_list)
	# Unicorn output file to write the generated output to
	output_file_name = inst_test_suite.get_hexstring()
	op_fileptr = open( output_file_name,"w")
	op_fileptr.write ("fname="+ output_file_name +"\n")
	op_fileptr.write("input_bitstring=" + inst_test_suite.get_pvs_bitstring() +"\n")
	# Run the instruction 
	test_arm64(bytes(bytecode), op_fileptr, reg_list)
'''
