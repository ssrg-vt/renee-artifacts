open Obj
open Str
open Printf
open Int64
open Utils
open Lib_spec
   
(* Specific definitions to generate test bit vectors *)

let ith_int num i = if num land (1 lsl i) <> 0 then 1 else 0

let int_to_bit_arr len num = Array.init len (ith_int num)

                           
let gen_random_vector max_seq_length =
  let length = Random.int max_seq_length in
  let sectors = div_ceil length baseVecLength in
  let arr = Array.make length 0 in
  for i = 0 to sectors - 1 do
    if i == sectors - 1 then
      let len = length - i * baseVecLength in
      let max_num = int_of_float (2.0 ** (float_of_int len)) in
      let num = Random.int max_num in
      let ith_arr = int_to_bit_arr len num in
      Array.blit ith_arr 0 arr (i * baseVecLength) len
    else
      let num = Random.int baseVecNum in
      let ith_arr = int_to_bit_arr baseVecLength num in
      Array.blit ith_arr 0 arr (i * baseVecLength) baseVecLength;
  done;
  arr

let bool_of_int = function
  | 0 -> "false"
  | _ -> "true"


       
let bit_of_int = function
  | 0 -> "FALSE"
  | _ -> "TRUE"

       
let bit_of_intstring = function
  | "0" -> "FALSE"
  | "1" -> "TRUE"
  | _ -> failwith "invalid bit value"

       
let int_of_char = function
  | '0' -> 0
  | '1' -> 1
  | _ -> failwith "invalid bit value"
       

(* Pretty print functions in ocaml and pvs *)

let string_of_char c =
  let str_c = string_of_int c in
  "char(" ^ str_c ^ ")"

  
let bit_arr_of_string str =
  let length = String.length str in
  if length == 0 then [||]
  else
    begin
      let arr = Array.make length 0 in
      for i = 0 to length - 1 do
        Array.set arr i (int_of_char (String.get str i))
      done;
      arr
    end
  
       
let make_sep_array len =
  let arr = Array.make (2*len-1) "" in
  for i = 0 to len - 2 do
    let str_i = sprintf "   %-4d" i in
    Array.set arr (2*i) str_i;
    Array.set arr (2*i+1) "|";
  done;
  let str_len_1 = sprintf "   %-4d" (len-1) in
  Array.set arr (2*len-2) str_len_1;
  arr
  

let string_of_vec arr =
  let len = Array.length arr in
  if len == 0 then
    "empty_bv"
  else
    if len == 1 then
      let str = sprintf "(LAMBDA (i:below(1)): TABLE\n    | i = 0 | %s ||\n    ENDTABLE)" (bit_of_int (Array.get arr 0)) in
      str
    else
      begin
        let index_arr = make_sep_array len in
        let indexes = Array.fold_left (^) "" index_arr in
        let values = Array.fold_left (separate "| ") "" (Array.map bit_of_int arr) in
        let str = sprintf "(LAMBDA (i:below(%d)): TABLE,\n    i |[%s]|\n       %s||\n    ENDTABLE)" len indexes values in
        str
      end
  

let string_of_ml_args arg_list =
  let result = String.concat " " (List.map parenth arg_list) in
  result

let string_of_pvs_args arg_list =
  let result = String.concat "" (List.map parenth arg_list) in
  result
    

let string_of_bool_list b_list =
  let b_length = List.length b_list in
  let result = ref "" in
  if b_length == 0 then
    result := "null"
  else
    result := "(: " ^ (String.concat ", " (List.map string_of_bool b_list)) ^ " :)";
  !result
      

let string_of_int_option i_opt =
  match i_opt with
  | None -> "None"
  | Some i -> "Some(" ^ string_of_int i ^ ")"
                                            
