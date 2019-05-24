
#!/usr/bin/env python
# Sample code for ARM64 of Unicorn. Nguyen Anh Quynh <aquynh@gmail.com>
# Python sample ported by Loi Anh Tuan <loianhtuan@gmail.com>

from __future__ import print_function
from unicorn import *
from unicorn.arm64_const import *
import sys
import codecs
import os

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
def test_arm64(ARM64_CODE):
    print("Emulate ARM64 code")
    try:
        # Initialize emulator in ARM mode
        mu = Uc(UC_ARCH_ARM64, UC_MODE_ARM)

        # map 2MB memory for this emulation
        mu.mem_map(ADDRESS, 2 * 1024 * 1024)

        # write machine code to be emulated to memory
        mu.mem_write(ADDRESS, ARM64_CODE)

        # initialize machine registers
 	#mu.reg_write(UC_ARM64_REG_X0, 0x1234)
        mu.reg_write(UC_ARM64_REG_X2, 0x2)
	print ("R2_pre = "+ convert_to_bvec("0x2",64))
        mu.reg_write(UC_ARM64_REG_X5, 0x1)
	print ("R5_pre = "+ convert_to_bvec("0x1",64))
	#mu.reg_write(UC_ARM64_REG_NZCV, 0x0)
        #mu.reg_write(UC_ARM64_REG_APSR, 0xFFFFFFFF) #All application flags turned on

        # tracing all basic blocks with customized callback
        mu.hook_add(UC_HOOK_BLOCK, hook_block)

        # tracing all instructions with customized callback
        mu.hook_add(UC_HOOK_CODE, hook_code, begin=ADDRESS, end=ADDRESS)
	nzcv = mu.reg_read(UC_ARM64_REG_NZCV)
	pc = mu.reg_read(UC_ARM64_REG_PC)
	print("PC_pre = 0x%x" %pc)
	print("NZCV_pre = 0x%x" %nzcv)
        # emulate machine code in infinite time
        mu.emu_start(ADDRESS, ADDRESS + len(ARM64_CODE))

        # now print out some registers
        #print(">>> Emulation done. Below is the CPU context")
        #print(">>> As little endian, X15 should be 0x78:")

        r2 = mu.reg_read(UC_ARM64_REG_X2)
	#nzcv = mu.reg_read(UC_ARM64_REG_NZCV)
	pc = mu.reg_read(UC_ARM64_REG_PC)
	r5 = mu.reg_read(UC_ARM64_REG_X5)
        print("R2_post = 0x%x" %r2)
	print("R5_post = 0x%x" %r5)
	print("NZCV_post = 0x%x" %nzcv)
	print("PC_post = 0x%x" %pc)

    except UcError as e:
        print("ERROR: %s" % e)


if __name__ == '__main__':
	# code to be emulated
	l = [b"\x42\x00\x05\xea", b"\x42\x00\x05\xeb"]
	for item in l:
		ARM64_CODE = bytes(item)
		test_arm64(ARM64_CODE)

