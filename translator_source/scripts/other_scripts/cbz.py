import random
import os
import subprocess

def generate_rand(len_rand):
  s=""
  for i in range(len_rand):
      s+=str(random.randint(0,1))
  return s



def main(i):
    current_path = os.getcwd().strip() +"/"
    output_dir = "/script_results/" 
    output_file_path = current_path + output_dir
    fname = "cbz_test_" + str(i) +  ".pvs"
    theory_name = fname.replace(".pvs","")
    ffff="11111111"
    cbz_str1 = "10110100" 
    cbz_str2 = generate_rand(19)
    cbz_str3 = generate_rand(5)
    next = ffff + generate_rand(56)
    next_hex = subprocess.check_output(["rax2", str("0b" + next)])
    fail = ffff + generate_rand(56)
    fail_hex = subprocess.check_output(["rax2", str("0b" + fail)])
    Rn = int (cbz_str3, 2)
    reg_value = generate_rand(64)
    reg_value_hex = subprocess.check_output(["rax2", str("0b" + reg_value)])

    cbz_str = cbz_str1 + cbz_str2 + cbz_str3
    cbz_str = cbz_str[::-1]    
    
    output_file = open (output_file_path + fname , "w")
    output_file.write(theory_name  +" : THEORY\n")
    output_file.write("\tBEGIN\n\n")
    output_file.write("\tIMPORTING rsl@arm_state, rsl@cbz\n\n")
    output_file.write("\t\tX_sts : [ below(32) -> bvec[64] ]  = init`X\n\n")
    output_file.write("\t\tp    :  s = init with  [ `X("+ str(Rn) + ") := " + str(reg_value_hex) + "   ]\n\n")  
    output_file.write("\t\tcbz_1 : Theory = cbz [ p ] {{ Diag:= bv[32](0b" + cbz_str + ")" + ",\n\t\t\t\t\t      next:=  " + next_hex + " " +  ",\n\t\t\t\t\t      fail:= " + fail_hex +"}}\n\n")
    output_file.write("\ttest1 : lemma  cbz_1.post`PC`b = "+ next_hex + "  or \n" )
    output_file.write("\t               cbz_1.post`PC`b = "+ fail_hex + "  \n\n" )
    output_file.write("%|- p_TCC1         : PROOF\n")
    output_file.write("%|- cbz_1_TCC*     : PROOF (eval-formula)\n")
    output_file.write("%|- QED\n\n")
    output_file.write("%|- test* : PROOF ( cbz )\n")
    output_file.write("%|- QED\n\n")
    output_file.write("End "+ theory_name)


if __name__== "__main__":
  for i in range(30):
    main(i)
