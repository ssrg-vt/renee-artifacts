open Int64
   
open Pset
   
open Utils
   

let pvsStrategies = [("OPEV_Value", "arith-strat \"unsigned\""); ("OPEV_Basic", "grind")]

               
let big_int_of_int = [("OPEV_Value", "Big_int_Z.big_int_of_int"); ("OPEV_Basic", "Nat_big_num.of_int")]
                
let string_of_big_int = [("OPEV_Value", "Big_int_Z.string_of_big_int"); ("OPEV_Basic", "Nat_big_num.to_string")]
                      
                      
let vbit_of_int = function
  | 0 -> "Vzero"
  | _ -> "Vone"              

       
let string_of_bits arr =
  let result = "[|" ^ (String.concat "; " (Array.to_list (Array.map vbit_of_int arr))) ^ "|]" in
  result

  
let string_of_ml_vec arr = "Vvector(" ^ (string_of_bits arr) ^ ", 0, true)"

       
type 'a set = 'a Pset.set

let set_fold = Pset.fold
             
             
let emptySet = "(Pset.empty compare)"

let setAdd x s = "Pset.add " ^ x ^ " (" ^ s ^ ")"
         
let rat_of_ints = "Rational.QI.of_ints "

let string_of_rat = "Rational.QI.to_string"

let string_of_vbit = "Sail_values.string_of_bit"

let string_of_value = "Sail_values.string_of_value"

    
