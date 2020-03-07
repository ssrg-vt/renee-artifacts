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


inst_bitstring = "10001010000000110000000001000010"

def create_bytes_array():
    int_list = []
    # chop the bitsring into 8 bits at a time convert to int and add to a list
    for i in range(0, 32, 8):
        int_list.append(int((inst_bitstring[i:i+8]), 2))
    # convert the list to a bytearray
    temp = int_list
    # bytestr = temp[::-1]
    return temp

ans = create_bytes_array()
bytecode = bytearray(ans)
print("$$$", ans)
