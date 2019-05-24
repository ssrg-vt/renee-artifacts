import random
import os

#let offset = LSL(64,12,v`imm,3 ) in
#let address = R_n_value + offset in 
#if address in [ , ] (mem-region used for emulation)
#   print the test lemma.   
#   The test lemma format is as follows:

def zero_extend_64(input_bvec,width):
  #padded_format = '{:0' +str(final_len) +'d}'
  return "{0:0>{wid}}".format(input_bvec,wid=width)

  #return input_bvec.zfill(final_len)

def generate_rand(len_rand):
  s=""
  for i in range(len_rand):
      s+=str(random.randint(0,1))
  return s

def LSL(bvec, shift_value):
  if shift_value == 0:
    return bvec
  else:
    result = LSL_C(bvec, shift_value)
    return result

def LSL_C(bvec, shift_value):
  if shift_value > 0:
    extended_x = zeros(shift_value)

def zeros(str_len):
  s = ""
  for i in range(str_len):
    s = s + "0"
  return s 


def main():
    print zero_extend_64("111010",64)
    current_path = os.getcwd().strip() +"/"
    output_dir = "/script_results/" 
    output_file_path = current_path + output_dir
    #fname = "br_test_" + str(i) +  ".pvs"
    #theory_name = fname.replace(".pvs","")
    output_file = open("ldr_man_test.pvs","w")
    output_file.write("ldr_man_test: Theory")
    output_file.write("\t\tbegin")
    output_file.write("\t\timporting rsl@ldr_imm_gen")
    output_file.write("\tX_sts   = init`X with [  (n):= bv--,")
    output_file.write("\t\t\t\t\t\t\t(t):= bv(--)    ]")
    output_file.write("\tMem_sts = init`Mem with [ `Mem(address):= 0x2 ] %%(0x2 %can be any random bvec[64])")
    output_file.write("\tp: s = init with [ `X:= X_sts ,`Mem := Mem_sts]")
    output_file.write("\tldr_1 : Theory = ldr_imm_gen[p] with {{ Diag:= --- }}")
    output_file.write("\ttest_1: lemma ldr_1.post`X(t) = 0x2 % whatever random")
    output_file.write("\t\tvalue generated at line 9")
    output_file.write("\ttest_2: conc_test_1.u = u1 => ldr_1.post`X(t):= 0x2 % % whatever random") 
    output_file.write("\t\tvalue generated at line 9")	   
    output_file.write("%|- test_*: Proof (ldr_imm_gen) QED")

if __name__== "__main__":
  #for i in range(300):
    main()