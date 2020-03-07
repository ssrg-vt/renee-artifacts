open Topdirs
open Toploop
open Lexing
open Format
open Unix
open Str
open Yojson.Basic.Util
open Printf

(* Global variables *)
let baseVecLength = 16

let baseVecNum = int_of_float (2.0 ** (float_of_int baseVecLength))

(* General functions *)
let rand_integer lower upper = begin
  let max_num = upper - lower in
  let rand_num = Random.int max_num in
  rand_num - lower
end

let div_ceil x y = (x / y) + (if (x mod y) == 0 then 0 else 1)


let separate sep a b = a ^ sep ^ b

let parenth a = "(" ^ a ^ ")"

let rec sublist ls start len =
  match ls with
  | [] -> []
  | x::xs -> if len == 0 then []
             else
               if start == 0 then x::(sublist xs start (len - 1))
               else
                 sublist xs (start - 1) len


let rec remove_last ls =
  match ls with
  | [] -> []
  | [x] -> []
  | x::y::xs -> x::(remove_last (y::xs))


let unique ls =
  let ls_tbl = Hashtbl.create (List.length ls) in
  List.filter (fun x -> let tmp = not (Hashtbl.mem ls_tbl x) in
                        Hashtbl.replace ls_tbl x ();
                        tmp) ls     
  
let init_list n =
  let rec init_list_rec n result =
    if n == 0 then result
    else
      init_list_rec (n - 1) ((n - 1)::result) in
  init_list_rec n []

let make_list n iv =
  let rec make_list_rec n iv result =
    if n == 0 then result
    else
      make_list_rec (n-1) iv (iv::result) in
  make_list_rec n iv []


let startswith sub str =
  let str_reg = if sub = "[" then Str.regexp "\[" else Str.regexp sub in
  Str.string_match str_reg str 0

  
let endswith sub str =
  let str_reg = if sub = "[" then Str.regexp "\[" else Str.regexp sub in
  Str.string_match str_reg str (String.length str - String.length sub)

  
let contains str sub =
  let str_reg = Str.regexp_string sub in
  try
    ignore (Str.search_forward str_reg str 0);
    true
  with
    Not_found -> false

let is_uppercase s =
  String.length s == 1 && Str.string_match (Str.regexp "[A-Z]") s 0

let is_capitalized s =
  Str.string_match (Str.regexp "[A-Z]") s 0

let int_pow =
    "fun x y ->
    let rec int_pow x = (function
      | 0 -> 1
      | 1 -> x
      | n -> let tmp = int_pow x (n / 2) in
             tmp * tmp * (if n mod 2 = 0 then 1 else x)) in
    int_pow x y"
  
let parseFromString sep str parseFunc =
  let strs = Str.split (Str.regexp sep) str in
  let result = List.map parseFunc strs in
  result


let parseStringBK str bkleft bkright sep =
  let sep_first = String.sub sep 0 1 in
  let sep_len = String.length sep in
  let toContinue = ref false in
  let idx = ref 0 in
  let len = String.length str in
  let bk_count = ref 0 in
  let curr = ref "" in
  let result = ref [] in
  while !idx < len do
    let c = String.sub str !idx 1 in
    if String.equal c bkleft then
      begin
        bk_count := !bk_count + 1;
        curr := !curr ^ c;
        toContinue := true;
        idx := !idx + 1
      end
    else if String.equal c bkright then
      begin
        curr := !curr ^ c;
        bk_count := !bk_count - 1;
        if !bk_count == 0 then
          toContinue := false;
        idx := !idx + 1
      end
    else if String.equal c sep_first && String.length str >= !idx + sep_len && String.equal (String.sub str !idx sep_len) sep then
      if !toContinue then
        begin
          curr := !curr ^ c;
          idx := !idx + 1
        end
      else
        begin
          curr := String.trim !curr;
          result := !result @ [!curr];
          curr := "";
          idx := !idx + sep_len
        end
    else
      begin
        curr := !curr ^ c;
        idx := !idx + 1
      end
  done;
  result := !result @ [(String.trim !curr)];
  !result


let split r s =
  if r = "[" then
    Str.split (Str.regexp "\[") s
  else if r = "." then
    Str.split (Str.regexp "\.") s
  else
    Str.split (Str.regexp r) s

let get_split_elem r s i =
  let ss = split r s in
  if i >= List.length ss then ""
  else
    List.nth (split r s) i

    
let bounded_split r s i =
  if r = "[" then
    List.nth (Str.bounded_split (Str.regexp "\[") s 2) i
  else
    List.nth (Str.bounded_split (Str.regexp r) s 2) i

let map_split_result = function
  | Text s -> s
  | Delim s -> s

let full_split r s =
  if String.equal r "[" then
    List.map map_split_result (Str.full_split (Str.regexp "\[") s)
  else
    List.map map_split_result (Str.full_split (Str.regexp r) s)
           
let get_bk_elem bkleft bkright s =
  String.concat "" (remove_last (full_split bkright (bounded_split bkleft s 1)))

let split_first sub str =
  String.concat "" (List.tl (full_split sub str))
  
let rsplit_last sub str =
  String.concat "" (remove_last (full_split sub str))

let sub_num sub str =
  let strs = split sub str in
  let str_num = List.length strs in
  let st = if startswith sub str then 1 else 0 in
  let ed = if endswith sub str then 1 else 0 in
  st + ed + str_num - 1
  
  
(* Update a json file *)

let json_to_list = Yojson.Basic.Util.to_list
let json_to_string = Yojson.Basic.Util.to_string
let json_to_assoc = Yojson.Basic.Util.to_assoc
                  
let updateJson json destKey newValue = 
  let newjson = match json with
  | `Bool b -> `Bool b
  | `Float f -> `Float f
  | `Int i -> `Int i
  | `List jl -> `List jl
  | `Null -> `Null
  | `String st -> `String st
  | `Assoc kvlist -> 
     `Assoc (List.map (fun (key, value) -> 
             match value with
             | `String v when String.equal key destKey -> (key, `String newValue)
             | _ -> (key, value)) kvlist) in
  newjson

(* Load the content of a file to string *)
     
let load_file fName =
  let ic = open_in fName in
  let length = in_channel_length ic in
  let result = Bytes.create length in
  really_input ic result 0 length;
  close_in ic;
  Bytes.to_string result
  
(* Evaluation of ocaml command based on toplevel execution *)
  
let is_ready_for_read fd =
  let fd_for_read, _, _ = Unix.select [fd] [] [] 0.001 in
  fd_for_read <> []

let string_of_fd fd =
  let buf = Buffer.create 1024 in
  let s = Bytes.create 256 in
  while is_ready_for_read fd do
    let r = Unix.read fd s 0 256 in
    Buffer.add_subbytes buf s 0 r
  done;
  Buffer.contents buf

let init_stdout = Unix.dup Unix.stdout
let init_stderr = Unix.dup Unix.stderr

let flush_std_out_err () =
  Format.pp_print_flush Format.std_formatter ();
  flush Pervasives.stdout

let get_out_err_and_restore out_in out_out err_in err_out =
    let out = string_of_fd out_in in
    Unix.close out_in;
    Unix.close out_out;
    Unix.dup2 init_stdout Unix.stdout;
    let err = string_of_fd err_in in
    Unix.close err_in;
    Unix.close err_out;
    Unix.dup2 init_stderr Unix.stderr;
    (out, err) 

    
let eval code =
  flush_std_out_err ();
  let (out_in, out_out) = Unix.pipe() in
  Unix.dup2 out_out Unix.stdout; (* Unix.stdout → out_out *)
  let (err_in, err_out) = Unix.pipe() in
  Unix.dup2 err_out Unix.stderr; (* Unix.stderr → err_out *)
  try
    let lexbuf = Lexing.from_string code in
    let phrase = !Toploop.parse_toplevel_phrase lexbuf in
    let result = Toploop.execute_phrase true Format.str_formatter phrase in
    let out, err = get_out_err_and_restore out_in out_out err_in err_out in
    if result then (out, 0) else (out, 1)
  with
  | e ->
     let out, err = get_out_err_and_restore out_in out_out err_in err_out in
     (err, -1)

let eval_type code =
  flush_std_out_err ();
  let (out_in, out_out) = Unix.pipe() in
  Unix.dup2 out_out Unix.stdout; (* Unix.stdout → out_out *)
  let (err_in, err_out) = Unix.pipe() in
  Unix.dup2 err_out Unix.stderr; (* Unix.stderr → err_out *)
  try
    let lexbuf = Lexing.from_string code in
    let phrase = !Toploop.parse_toplevel_phrase lexbuf in
    let result = Toploop.execute_phrase true Format.std_formatter phrase in
    let out, err = get_out_err_and_restore out_in out_out err_in err_out in
    if result then (out, 0) else (out, 1)
  with
  | e ->
     let out, err = get_out_err_and_restore out_in out_out err_in err_out in
     (err, -1)

  
(* Functions for calling external commands *)
     
let check_exit_status = function
  | Unix.WEXITED 0 -> 0
  | _ -> -1

let syscall cmd =
  let ic = Unix.open_process_in cmd in
  let buf = Buffer.create 16 in
  (try
     while true do
       Buffer.add_channel buf ic 1
     done
   with End_of_file -> ());
  let _ = Unix.close_process_in ic in
  (Buffer.contents buf)

