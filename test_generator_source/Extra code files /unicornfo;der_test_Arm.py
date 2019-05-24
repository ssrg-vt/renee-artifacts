
# Sample code for ARM64 of Unicorn. Nguyen Anh Quynh <aquynh@gmail.com>
# Python sample ported by Loi Anh Tuan <loianhtuan@gmail.com>

from __future__ import print_function
from unicorn import *
from unicorn.arm64_const import *
import sys
import codecs
import os
import master_test

# memory address where emulation starts
ADDRESS    = 0x10000


# callback for tracing basic blocks
def hook_block(uc, address, size, user_data):
    return 0
    #print(">>> Tracing basic block at 0x%x, block size = 0x%x" %(address, size))


# callback for tracing instructions
def hook_code(uc, address, size, user_data):
    return 0
    #print(">>> Tracing instruction at 0x%x, instruction size = 0x%x" %(address, size))

# a custom fnc to input a hex string and return the 64 bit bvec in the PVS bvec form (LSB : MSB)
def convert_to_bvec(hex_num, leading_zeros):
	return ("bv(0b" + str(bin(int(hex_num,16))[2:].zfill(leading_zeros)[::-1]) + ")")

# Test ARM64
def test_arm64(ARM64_CODE,ff):
    try:
        # Initialize emulator in ARM mode
        mu = Uc(UC_ARCH_ARM64, UC_MODE_ARM)

        # map 2MB memory for this emulation
        mu.mem_map(ADDRESS, 2 * 1024 * 1024)

        # write machine code to be emulated to memory
        mu.mem_write(ADDRESS, ARM64_CODE)

        # initialize machine registers
 	#mu.reg_write(UC_ARM64_REG_X0, 0x1234)
        mu.reg_write(UC_ARM64_REG_X30, 0x2)
	print ("R30_pre = "+ convert_to_bvec("0x2",64))
        mu.reg_write(UC_ARM64_REG_X8, 0xf)
        print ("R8_pre = "+ convert_to_bvec("0xf",64))
	mu.reg_write(UC_ARM64_REG_X7, 0xf)
        print ("R7_pre = "+ convert_to_bvec("0xf",64))
	#mu.reg_write(UC_ARM64_REG_NZCV, 0x0)
        #mu.reg_write(UC_ARM64_REG_APSR, 0xFFFFFFFF) #All application flags turned on

        # tracing all basic blocks with customized callback
        mu.hook_add(UC_HOOK_BLOCK, hook_block)

        # tracing all instructions with customized callback
        mu.hook_add(UC_HOOK_CODE, hook_code, begin=ADDRESS, end=ADDRESS)
	nzcv = mu.reg_read(UC_ARM64_REG_NZCV)
	pc = mu.reg_read(UC_ARM64_REG_PC)
        # emulate machine code in infinite time
        mu.emu_start(ADDRESS, ADDRESS + len(ARM64_CODE))

        # now print out some registers
        #print(">>> Emulation done. Below is the CPU context")
        #print(">>> As little endian, X15 should be 0x78:")

        r30 = mu.reg_read(UC_ARM64_REG_X30)
	#nzcv = mu.reg_read(UC_ARM64_REG_NZCV)
	pc = mu.reg_read(UC_ARM64_REG_PC)
	r8 = mu.reg_read(UC_ARM64_REG_X8)
	r7 = mu.reg_read(UC_ARM64_REG_X7)

        print("R30_post = 0x%x" %r30)
	print("R8_post = 0x%x" %r8)
	print("R7_post = 0x%x" %r7)
	print("NZCV_post = 0x%x" %nzcv)
	print("PC_post = 0x%x" %pc)


    except UcError as e:
        print("ERROR: %s" % e)


if __name__ == '__main__':
	# code to be emulated
	#l = [b"\x42\x00\x05\xea", b"\x42\x00\x05\xeb", "\x8f\x07\x59\xeb", b"\x8f\x07\x59\xeb", b"\x8f\x07\x59\xeb"]
	
	#inst_test_suite = master_test.inst_validation('')
	#inst_test_suite.extract_fields()
	#for i in range(1):				
	#inst_test_suite.generate_validation_file()
	#int_list = inst_test_suite.get_bytestr()
	#b = bytearray([235, 82, 198, 194])
	#fname = ["eb0889b0"]
	item = b'\xfe\xa8\x88\xeb'
	ff =open("name","w")
	test_arm64(bytes(item), ff)

