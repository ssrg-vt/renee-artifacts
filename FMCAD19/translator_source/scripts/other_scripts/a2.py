import random
import os

def generate_rand(len_rand):
    s=""
    for i in range(len_rand):
        s+=str(random.randint(0,1))
    return s

def main(i):
    current_path = os.getcwd().strip() +"/"
    output_dir = "/script_results/" 
    output_file_path = current_path + output_dir
    fname = "ret_test_" + str(i) +  ".pvs"
    theory_name = fname.replace(".pvs","")
    ret_str1 = "1101011001011111000000" 
    ret_str2 = generate_rand(5)
    ret_str3 = "00000"
    Rn = int (ret_str2, 2)
    print Rn
    reg_value = generate_rand(64)
    print reg_value
    ret_str = ret_str1 + ret_str2 + ret_str3
    ret_str = ret_str[::-1]    
    
    output_file = open (output_file_path + fname , "w")
    output_file.write(theory_name   +    ": THEORY\n\n")
    output_file.write("\tBEGIN\n\n")
    output_file.write("\tIMPORTING rsl@arm_state, rsl@ret\n\n")
    output_file.write("\t\tX_sts : [ below(32) -> bvec[64] ]  = init`X\n\n")
    output_file.write("\t\tp    :  s = init with  [ `X("+ str(Rn) + ") := bv[64]( 0b" + str(reg_value) + " )  ]\n\n")  
    output_file.write("\t\tret_1 : Theory = ret [ p ] {{ Diag:= bv[32](0b" + ret_str + ") }}\n\n")
    output_file.write("\ttest1 : lemma  ret_1.post`PC`b = bv[64](0b"+ str(reg_value) +" ) \n\n" )
    output_file.write("%|- p_TCC1         : PROOF\n")
    output_file.write("%|- ret_1_TCC*     : PROOF\n")
    output_file.write("%|- test1_TCC1     : PROOF (eval-formula)\n")
    output_file.write("%|- QED\n\n")
    output_file.write("%|- test1 : PROOF ( ret )\n")
    output_file.write("%|- QED\n\n")
    output_file.write("End " +  theory_name  )


if __name__== "__main__":
  for i in range(300):
    main(i)