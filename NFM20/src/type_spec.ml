open Obj
open Str
open Printf
open Int64
open Utils
open Lib_spec
open Pretty_print

(* Intermediate type definitions and corresponding functions *)

type pType =
  | PEmpty
  | PBasic of pBasic
  | PComplex of pComplex
  | PDef of pDef
  | PExt of pExt
  | PSpec of pSpec
and pBasic =
  | PUnit
  | PBool
  | PChar
  | PNat
  | PInt
  | PReal
and pComplex =
  | PString
  | PList of pType
  | PTuple of pType list
and pDef =
  | PBit
  | PBvec
  | PRat
  | PSet of pType
  | PRecord of (string * pType)
  | PDataType of (string * pType)
  | PField of (string * pType)
and pExt =
  | PBigInt
  | PBigNat
  | PInt32
  | PInt64
and pSpec =
  | PFunc of pType list
  | PType of (string * pType * pType)
  | PTVar of string
  | PNVar of int
  

let rec string_of_typename lenFinSeq tp =
  match tp with
  | PEmpty -> ""
  | PBasic pb -> (match pb with
                  | PUnit -> "Unit"
                  | PBool -> "bool"
                  | PChar -> "char"
                  | PNat -> "nat"
                  | PInt -> "int"
                  | PReal -> "real"
                 )
  | PComplex pc -> (match pc with
                    | PString -> "string"
                    | PList pt -> "list[" ^ (string_of_typename lenFinSeq pt) ^ "]"
                    | PTuple pts -> "[" ^ (String.concat ", " (List.map (string_of_typename lenFinSeq) pts)) ^ "]"
                   )
  | PDef pd -> (match pd with
                | PBit -> "bit"
                | PBvec -> "bvec[" ^ (string_of_int lenFinSeq) ^ "]"
                | PRat -> "rat"
                | PSet pt -> "set[" ^ (string_of_typename lenFinSeq pt) ^ "]"
                | PRecord (name, pt) -> if pt = PEmpty then name
                                        else name ^ "[" ^ (string_of_typename lenFinSeq pt) ^ "]"
                | PDataType (name, pt) -> if pt = PEmpty then name
                                          else name ^ "[" ^ (string_of_typename lenFinSeq pt) ^ "]"
                | PField (name, pt) -> name
               )
  | PExt pe -> (match pe with
                | PBigInt -> "int"
                | PBigNat -> "nat"
                | PInt32 -> "int32"
                | PInt64 -> "int64"
               )
  | PSpec ps -> (match ps with
                 | PFunc pts -> String.concat "->" (List.map (string_of_typename lenFinSeq) pts)
                 | PType (name, pt1, pt2) -> if pt1 = PEmpty then name
                                             else name ^ "[" ^ (string_of_typename lenFinSeq pt2) ^ "]"
                 | PTVar tv -> tv
                 | PNVar nv -> string_of_int nv
                )

       
let tv_tbl = Hashtbl.create 10
let max_num_variable = 10
           
let rec list_of_type_variables tp =
  match tp with
  | PEmpty -> []
  | PBasic _ -> []
  | PComplex pc -> (match pc with
                    | PString -> []
                    | PList pt -> list_of_type_variables pt
                    | PTuple pts -> List.flatten (List.map list_of_type_variables pts))
  | PDef pd -> (match pd with
                | PBit -> []
                | PBvec -> []
                | PRat -> []
                | PSet pt -> list_of_type_variables pt
                | PRecord (name, pt) -> list_of_type_variables pt
                | PDataType (name, pt) -> list_of_type_variables pt
                | PField (name, pt) -> list_of_type_variables pt)
  | PExt _ -> []
  | PSpec ps -> (match ps with                  
                 | PFunc pts -> List.flatten (List.map list_of_type_variables pts)
                 | PType (name, pt1, pt2) -> []
                 | PTVar tv -> [tv]
                 | PNVar nv -> [])
              

let rec parseFuncType type_class_tbl type_tbl libName mlType curType =
  (* printf "ml type: %s,   pvs type: %s\n" mlType curType; *)
  if curType = "" then PEmpty
  else if curType = "Unit" then PBasic PUnit
  else if curType = "bool" then PBasic PBool
  else if curType = "char" then PBasic PChar
  else if curType = "real" then PBasic PReal
  else if curType = "string" then PComplex PString
  else if curType = "bit" then PDef PBit
  else if curType = "rat" || curType = "rational" then PDef PRat
  else if Utils.is_capitalized curType then
    PSpec (PTVar curType)
  else if startswith "[" curType then
    if contains curType "->" then
      begin
        let ts = String.sub curType 1 ((String.length curType) - 2) in
        let remove_outer_bk s = let s' = if sub_num "[" s > sub_num "]" s then split_first "[" s else s in
                                let s'' = if sub_num "]" s' > sub_num "[" s' then rsplit_last "]" s' else s' in
                                s'' in
        let tsList =  (List.map (remove_outer_bk) (Utils.split "->" ts)) in
        let tys =  if (mlType = "" || startswith "'" mlType) then
                     List.map (parseFuncType type_class_tbl type_tbl libName "") tsList
                   else
                     let mlList = List.map (String.trim) (Utils.split "->" (String.sub mlType 1 ((String.length mlType) - 2))) in
                     if List.length tsList == List.length mlList then
                       List.map2 (parseFuncType type_class_tbl type_tbl libName) mlList tsList
                     else
                       List.map (parseFuncType type_class_tbl type_tbl libName "") tsList in
        PSpec (PFunc tys)
      end
    else
      begin
        let ts = String.sub curType 1 ((String.length curType) - 2) in
        let tys = if (mlType = "" || startswith "'" mlType) then
                    List.map (parseFuncType type_class_tbl type_tbl libName "") (Utils.split "," ts)
                  else
                    List.map2 (parseFuncType type_class_tbl type_tbl libName) (List.map (String.trim) (Utils.split "*" (String.sub mlType 1 ((String.length mlType) - 2)))) (Utils.split "," ts) in
        PComplex (PTuple tys)
      end
  else if contains curType "->" then
    begin
      let tys = List.map (parseFuncType type_class_tbl type_tbl libName mlType) (Utils.split "->" curType) in
      PSpec (PFunc tys)
    end
  else if (curType = "nat" || curType = "posnat" || startswith "below" curType || startswith "above" curType || startswith "upto" curType || startswith "upfrom" curType || curType = "posint") && (mlType = "" || mlType = "int" || mlType = "(int)" || startswith "'" mlType || mlType = "nat") then PBasic PNat
  else if (curType = "int" || curType = "nzint") && (mlType = "" || mlType = "int" || mlType = "(int)" || startswith "'" mlType) then PBasic PInt
  else if (curType = "nat" || curType = "posnat" || startswith "below" curType || startswith "above" curType || startswith "upto" curType || startswith "upfrom" curType || curType = "posint") && (contains mlType "32") then PExt PInt32
  else if (curType = "nat" || curType = "posnat" || startswith "below" curType || startswith "above" curType || startswith "upto" curType || startswith "upfrom" curType || curType = "posint") && (contains mlType "64") then PExt PInt64
  else if (curType = "int" || curType = "nzint") && (contains mlType "32") then PExt PInt32
  else if (curType = "int" || curType = "nzint") && (contains mlType "64") then PExt PInt64
  else if (curType = "int" || curType = "nzint") then PExt PBigInt
  else if curType = "nat" || curType = "posnat" || startswith "below" curType || startswith "above" curType || startswith "upto" curType || startswith "upfrom" curType || curType = "posint" then PExt PBigNat  
  else if startswith "bvec" curType then PDef PBvec
  else if startswith "list\[" curType || curType = "list" then
    let ts = String.sub curType 5 ((String.length curType) - 6) in
    let mlTS = if (mlType = "" || startswith "'" mlType) then "" else String.sub mlType 0 ((String.length mlType) - 5) in
    PComplex (PList (parseFuncType type_class_tbl type_tbl libName mlTS ts))
  else if startswith "set\[" curType || curType = "set" then
    let ts = String.sub curType 4 ((String.length curType) - 5) in
    let mlTS = if (mlType = "" || startswith "'" mlType) then "" else String.sub mlType 0 ((String.length mlType) - 9) in
    PDef (PSet (parseFuncType type_class_tbl type_tbl libName mlTS ts))
  else
    try
      begin
        let tName = get_split_elem "[" curType 0 in
        let compName = libName ^ "@" ^ tName in
        let ty_class = Hashtbl.find type_class_tbl compName in
        if ty_class = "record" then
          if contains curType "[" then
            begin
              let tv = String.trim (get_bk_elem "[" "]" curType) in
              let mlTS = if mlType = "" || startswith "'" mlType then ""
                         else if contains mlType "(" then String.trim (rsplit_last ")" mlType)
                         else String.trim (rsplit_last " " mlType) in
              (* printf "Record: %s,  %s,  %s\n" tName tv mlTS; *)
              let vType = parseFuncType type_class_tbl type_tbl libName mlTS tv in
              PDef (PRecord (tName, vType))
            end
          else
            PDef (PRecord (tName, PEmpty))
        else if ty_class = "datatype" then
          begin
            if contains curType "[" then
              begin
                let tv = get_bk_elem "[" "]" curType in
                (* let tv = String.trim (get_split_elem tName curType 0) in *)
                let mlTS = if mlType = "" || startswith "'" mlType then ""
                       else if contains mlType "(" then String.trim (rsplit_last ")" mlType)
                       else String.trim (rsplit_last " " mlType) in
                let vType = parseFuncType type_class_tbl type_tbl libName mlTS tv in
                PDef (PDataType (tName, vType))
              end
            else
              PDef (PDataType (tName, PEmpty))
          end
        else
          begin
            let tDefs = Hashtbl.find type_tbl compName in
            let tDef = if List.length tDefs > 0 then List.nth tDefs 0 else "" in
            if List.length tDefs > 1 then
              let ntp = String.trim (List.nth tDefs 0) in
              let pt = parseFuncType type_class_tbl type_tbl libName "" ntp in
              let nv = Random.int max_num_variable in
              PSpec (PType (tName, pt, PSpec (PNVar nv)))
            else if tDef = "" then
              PSpec (PType (tName, PEmpty, PEmpty))
            else
              begin
                (* printf "User-defined type: %s\n" tDef; *)
                parseFuncType type_class_tbl type_tbl libName "" tDef
              end
          end
      end
    with Not_found -> if contains "," curType then
                        let tys = if (mlType = "" || startswith "'" mlType) then
                                    List.map (parseFuncType type_class_tbl type_tbl libName "") (Utils.split "," curType)
                                  else
                                    List.map2 (parseFuncType type_class_tbl type_tbl libName) (List.map (String.trim) (Utils.split "*" (String.sub mlType 1 ((String.length mlType) - 2)))) (Utils.split "," curType) in
                        PComplex (PTuple tys)
                      else
                        failwith ("parseFuncType: undefined behavior for the type " ^ curType)
       
let tv_inst_type key =
  if key == 0 then PBasic PBool
  else PBasic PNat
  
let inst_type_variable tv_list =
  for i = 0 to (List.length tv_list - 1) do
    let key = Random.int 2 in
    Hashtbl.replace tv_tbl (List.nth tv_list i) (tv_inst_type key)
  done;
  ()

let rec replace_type_variable tv_tbl tp =
  match tp with
  | PEmpty -> PEmpty
  | PBasic _ -> tp
  | PComplex pc -> (match pc with
                    | PString -> tp
                    | PList pt -> PComplex (PList (replace_type_variable tv_tbl pt))
                    | PTuple pts -> PComplex (PTuple (List.map (replace_type_variable tv_tbl) pts)))
  | PDef pd -> (match pd with
                | PSet pt -> PDef (PSet (replace_type_variable tv_tbl pt))
                | PRecord (name, pt) -> PDef (PRecord (name, replace_type_variable tv_tbl pt))
                | PDataType (name, pt) -> PDef (PDataType (name, replace_type_variable tv_tbl pt))
                | PField (name, pt) -> PDef (PField (name, replace_type_variable tv_tbl pt))
                | _ -> tp)
  | PExt _ -> tp
  | PSpec ps -> (match ps with
                 | PFunc pts -> PSpec (PFunc (List.map (replace_type_variable tv_tbl) pts))
                 | PTVar tv ->
                    begin
                      try
                        Hashtbl.find tv_tbl tv
                      with Not_found -> failwith ("replace_type_variable: cannot find the type inst for type " ^ tv)
                    end
                 | _ -> tp)

       
let map_func_pvs_ml name patList =
  if contains name "add" then "+"
  else if contains name "minus" then "-"
  else if contains name "mult" then "*"
  else if contains name "div" then "/"
  else if contains name "mod" then "mod"
  else if contains name "min" then "min"
  else if contains name "max" then "max"
  else if contains name "pow" then int_pow
  else if (contains name "eq" && contains name "less") || contains name "le" then "(<=)"
  else if contains name "less" || contains name "lt" then "(<)"
  else if (contains name "eq" && contains name "great") || contains name "ge" then "(>=)"
  else if contains name "great" || contains name "gt" then "(>)"
  else if contains name "eq" then "="
  else if contains name "not" then "not"
  else if contains name "and" then "&&"
  else if contains name "or" then "||"
  else if contains name "string_of_" then get_split_elem "." name 1
  else if contains name "succ" then "succ"
  else ""

  
let rec gen_type_arg lenFinSeq lower upper libName funcName type_class_tbl type_tbl field_tbl inst_tbl pattern_tbl curType nth ith =
  match curType with
  | PEmpty -> ("", "")
  | PBasic pb -> (match pb with
                  | PUnit -> ("()", "unit")
                  | PBool -> let bitArg = bool_of_int (Random.int 2) in (bitArg, bitArg)
                  | PChar -> let charArg = (Random.int 95) + 32 in
                             ("'" ^ Char.escaped (Char.chr charArg) ^ "'", string_of_char charArg)
                  | PNat -> let natArg = string_of_int (Random.int upper) in (natArg, natArg)
                  | PInt -> let intArg = string_of_int (rand_integer lower upper) in (intArg, intArg)
                  | PReal -> let numerator = rand_integer lower upper in
                             let denominator = let tmp = (rand_integer lower upper) in
                                               if tmp == 0 then (rand_integer lower upper)
                                               else tmp in
                             let strN = string_of_int numerator in
                             let strDN = string_of_int denominator in
                             let strNumerator = "(" ^ strN ^ ".0)" in
                             let strDenominator = "(" ^ strDN ^ ".0)" in
                             (strNumerator ^ "/." ^ strDenominator, strNumerator ^ "/" ^ strDenominator)                                    
                 )
  | PComplex pc -> (match pc with
                    | PString -> let seq_length = Random.int lenFinSeq in
                                 if seq_length == 0 then ("", "")
                                 else
                                   begin
                                     let indexList = init_list seq_length in
                                     let charList = List.map (fun i -> let str = Char.escaped (Char.chr ((Random.int 94) + 32)) in
                                                                       if str = "\"" then ("\\\"", "doublequote")
                                                                       else if str = "\\\'" then ("\\\'", "singlequote")
                                                                       else (str, "\"" ^ str ^ "\"")) indexList in
                                     let mlArg = "\"" ^ (String.concat "" (List.map fst charList)) ^ "\"" in
                                     let pvsArg = List.fold_right (fun x y -> let arg = (snd x) in
                                                                              if y = "\"\"" then arg
                                                                              else arg ^ " o (" ^ y ^ ")") charList "\"\"" in
                                     (mlArg, pvsArg)
                                   end
                    | PList pt -> let seq_length = Random.int lenFinSeq in
                                    if seq_length == 0 then
                                    let pt_name = string_of_typename seq_length pt in
                                    if pt_name = "" then
                                      ("[]", "null")
                                    else
                                      ("[]", "null[" ^ pt_name ^ "]")
                                  else
                                    begin
                                      let indexList = init_list seq_length in
                                      let tpList = List.map (gen_type_arg seq_length lower upper libName funcName type_class_tbl type_tbl field_tbl inst_tbl pattern_tbl pt nth) indexList in
                                      let mlList = "[" ^ (String.concat "; " (List.map fst tpList)) ^ "]" in
                                      let pvsList = "(: " ^ (String.concat ", " (List.map snd tpList)) ^ ":)" in
                                      (mlList, pvsList)
                                    end
                    | PTuple pts -> let tps = List.map (fun pt -> gen_type_arg lenFinSeq lower upper libName funcName type_class_tbl type_tbl field_tbl inst_tbl pattern_tbl pt nth ith) pts in
                                    let mlStr = "(" ^ (String.concat ", " (List.map fst tps)) ^ ")" in
                                    let pvsStr = "(" ^ (String.concat ", " (List.map snd tps)) ^ ")" in
                                    (mlStr, pvsStr)      
                   )
  | PDef pd -> (match pd with
                | PBit -> let bitArg = Random.int 2 in
                          (vbit_of_int bitArg, bit_of_int bitArg)
                | PBvec -> let arr = gen_random_vector lenFinSeq in
                           (string_of_ml_vec arr, string_of_vec arr)
                           
                | PRat -> let numerator = rand_integer lower upper in
                          let denominator = let tmp = (rand_integer lower upper) in
                                            if tmp == 0 then (rand_integer lower upper)
                                            else tmp in
                          let strN = string_of_int numerator in
                          let strDN = string_of_int denominator in
                          (rat_of_ints ^ " (" ^ strN ^ ") (" ^ strDN ^ ")", "(" ^ strN ^ ".0)" ^ "/" ^ "(" ^ strDN ^ ".0)")
                | PSet pt ->  let seq_length = Random.int lenFinSeq in
                               if seq_length == 0 then
                               let pt_name = string_of_typename seq_length pt in
                               if pt_name = "" then
                                 (emptySet, "emptyset")
                               else
                                 (emptySet, "emptyset[" ^ pt_name ^ "]")
                             else
                               begin
                                 let indexList = init_list seq_length in
                                 let tpList = List.map (gen_type_arg seq_length lower upper libName funcName type_class_tbl type_tbl field_tbl inst_tbl pattern_tbl pt nth) indexList in
                                 let ml_arg = List.fold_right setAdd (List.map fst tpList) emptySet in
                                 let pvs_arg = "{ x : " ^ (string_of_typename seq_length pt) ^ " | " ^ (String.concat " OR " (List.map (fun s -> "x = " ^ snd s) tpList)) ^ "}" in
                                 (ml_arg, pvs_arg)
                               end
                | PRecord (name, pt) -> let compName = libName ^ "@" ^ name in
                                        (* printf "name: %s, %s\n" compName (string_of_typename 0 pt); *)
                                        let insts = Hashtbl.find inst_tbl compName in
                                        let inst_filtered = List.filter (fun inst -> let (ity, _, instName) = inst in
                                                                                     let class_name = get_split_elem "_class" name 0 in
                                                                                     let ml_name = get_split_elem (String.capitalize class_name ^ "_") (get_split_elem "_dict" instName 0) 1 in
                                                                                     let ipt = parseFuncType type_class_tbl type_tbl libName ml_name ity in
                                                                                     (* printf "record: %s %s %s %s %s %s\n" name ity instName class_name ml_name (string_of_typename lenFinSeq ipt); *)
                                                                                     ipt = pt) insts in
                                        let inst_num = List.length inst_filtered in
                                        if inst_num > 0 then
                                          let key = Random.int inst_num in
                                          let inst = List.nth inst_filtered key in
                                          let (ity, iLib, instName) = inst in
                                          (iLib ^ "." ^ instName, instName)
                                        else
                                          begin
                                            let tv_inst_filtered = List.filter (fun inst -> let (ity, _, _) = inst in
                                                                                            let ipt = parseFuncType type_class_tbl type_tbl libName "" ity in
                                                                                            match ipt with
                                                                                            | PSpec ps -> (match ps with
                                                                                                           | PTVar tv -> true
                                                                                                           | _ -> false)
                                                                                            | _ -> false) insts in
                                            let inst_num = List.length tv_inst_filtered in
                                            if inst_num > 0 then
                                              let key = Random.int inst_num in
                                              let inst = List.nth tv_inst_filtered key in
                                              let (_, iLib, instName) = inst in
                                              (iLib ^ "." ^ instName, instName ^ "[" ^ (string_of_typename lenFinSeq pt) ^ "]")
                                            else
                                              begin
                                                let fields = Hashtbl.find field_tbl (libName ^ "@" ^ name) in
                                                let field_tvs = unique (List.flatten (List.map list_of_type_variables fields)) in
                                                let field_tv_tbl = Hashtbl.create 10 in
                                                (* printf "record without inst: %s, number of tvs: %d\n" name (List.length field_tvs); *)
                                                let _ = if List.length field_tvs > 1 then
                                                          let _ = match pt with
                                                            | PComplex PTuple tps -> List.iter2 (fun x y -> Hashtbl.add field_tv_tbl x y) field_tvs tps
                                                            | _ -> failwith ("gen_type_arg: the number of type varialbes for record " ^ name ^ " does not match the size of the parsed type") in
                                                          ()
                                                        else
                                                          List.iter (fun x -> Hashtbl.add field_tv_tbl x pt) field_tvs in
                                                let fields = List.map (replace_type_variable field_tv_tbl) fields in
                                                let field_num = List.length fields in
                                                let ml_record_arg = ref "{\n" in
                                                let pvs_record_arg = ref "(#\n" in
                                                for i = 0 to field_num - 1 do
                                                  let selected = List.nth fields i in
                                                  let field_name = string_of_typename lenFinSeq selected in
                                                  let ml_arg, pvs_arg = gen_type_arg lenFinSeq lower upper libName funcName type_class_tbl type_tbl field_tbl inst_tbl pattern_tbl selected nth ith in
                                                  ml_record_arg := !ml_record_arg ^ field_name ^ "=" ^ ml_arg ^ ";\n";
                                                  pvs_record_arg := !ml_record_arg ^ field_name ^ ":=" ^ pvs_arg ^ ",\n";
                                                done;
                                                ml_record_arg := rsplit_last ";" !ml_record_arg;
                                                pvs_record_arg := rsplit_last "," !pvs_record_arg;
                                                ml_record_arg := !ml_record_arg ^ "}";
                                                pvs_record_arg := !pvs_record_arg ^ "#)";
                                                (!ml_record_arg, !pvs_record_arg)
                                              end
                                          end
                | PDataType (name, pt) -> let fields = Hashtbl.find field_tbl (libName ^ "@" ^ name) in
                                          let field_tvs = unique (List.flatten (List.map list_of_type_variables fields)) in
                                          let field_tv_tbl = Hashtbl.create 10 in
                                          (* printf "datatype: %s, number of tvs: %d\n" name (List.length field_tvs); *)
                                          let _ = if List.length field_tvs > 1 then
                                                    let _ = match pt with
                                                      | PComplex PTuple tps -> List.iter2 (fun x y -> Hashtbl.add field_tv_tbl x y) field_tvs tps
                                                      | _ -> failwith ("gen_type_arg: the number of type varialbes for datatype " ^ name ^ " does not match the size of the parsed type") in
                                                    ()
                                                  else
                                                    List.iter (fun x -> Hashtbl.add field_tv_tbl x pt) field_tvs in
                                          let fields = List.map (replace_type_variable field_tv_tbl) fields in
                                          let field_num = List.length fields in
                                          let key = Random.int field_num in
                                          let selected = List.nth fields key in
                                          gen_type_arg lenFinSeq lower upper libName funcName type_class_tbl type_tbl field_tbl inst_tbl pattern_tbl selected nth ith
                | PField (name, pt) -> if pt = PEmpty then
                                         let pt_name = string_of_typename lenFinSeq pt in
                                         if pt_name = "" then
                                           (name, name)
                                         else
                                           (name, name ^ "[" ^ (string_of_typename lenFinSeq pt) ^ "]")
                                       else
                                         let field_arg = gen_type_arg lenFinSeq lower upper libName funcName type_class_tbl type_tbl field_tbl inst_tbl pattern_tbl pt nth ith in
                                         let ml_field_arg = name ^ " " ^ (fst field_arg) in
                                         let pvs_field_arg = name ^ "(" ^ (snd field_arg) ^ ")" in
                                         (ml_field_arg, pvs_field_arg)
               )
  | PExt pe -> (let bigint_of_int = snd (List.find (fun x -> fst x = libName) big_int_of_int) in
                match pe with
                | PBigInt -> let intArg = string_of_int (rand_integer lower upper) in
                             (bigint_of_int ^ " (" ^ intArg ^")", intArg)
                | PBigNat -> let natArg = string_of_int (Random.int upper) in
                             (bigint_of_int ^ " (" ^ natArg ^ ")", natArg)
                | PInt32 -> let intArg = string_of_int (rand_integer lower upper) in
                             ("(" ^ intArg ^"l)", intArg)
                | PInt64 -> let intArg = string_of_int (Random.int upper) in
                             ("(" ^ intArg ^ "L)", intArg))
  | PSpec ps -> (match ps with
                 | PFunc pts -> 
                    begin
                      try
                        let patList = Hashtbl.find pattern_tbl (libName, curType) in
                        if List.length patList == 0 then
                          begin
                            let ptList = ref [] in
                            Hashtbl.iter (fun (ln, k) v -> if not (ln = libName) then ()
                                                           else
                                                             begin
                                                               match k with
                                                               | PSpec (PFunc tps) ->
                                                                  begin
                                                                    if List.length pts == List.length tps then
                                                                      begin
                                                                        let pt_num = List.length pts in
                                                                        let pt_count = ref 0 in
                                                                        let tv_repl = Hashtbl.create 10 in
                                                                        for i = 0 to pt_num - 1 do
                                                                          let pt = List.nth pts i in
                                                                          let tp = List.nth tps i in
                                                                          if pt = tp then
                                                                            pt_count := !pt_count + 1
                                                                          else
                                                                            begin
                                                                              match tp with
                                                                              | PSpec (PTVar tv) ->
                                                                                 begin
                                                                                   try
                                                                                     let tv_inst = Hashtbl.find tv_repl tp in
                                                                                     if pt = tv_inst then
                                                                                       pt_count := !pt_count + 1
                                                                                   with Not_found -> begin
                                                                                       Hashtbl.add tv_repl tp pt;
                                                                                       pt_count := !pt_count + 1
                                                                                     end
                                                                                 end
                                                                              | _ -> ()
                                                                            end
                                                                        done;
                                                                        if !pt_count == pt_num then
                                                                          ptList := !ptList @ v
                                                                      end
                                                                    else ()
                                                                  end
                                                               | _ -> ()
                                                             end
                              ) pattern_tbl;
                            if List.length !ptList <> 0 then
                              begin
                                let ptNum = List.length !ptList in
                                let key = Random.int ptNum in
                                let pvs_name = List.nth !ptList key in
                                let ml_name = map_func_pvs_ml pvs_name pts in
                                if ml_name = "" then
                                  printf "undefined ml function in map_func_pvs_ml: pvs name: %s\n" pvs_name;
                                (ml_name, pvs_name)
                              end
                            else
                              begin
                                let patName = string_of_typename lenFinSeq curType in
                                (* printf "Undefined behavior for the function pattern: %s\n" patName; *)
                                let pt_num = List.length pts in
                                let pt_last = List.nth pts (pt_num - 1) in
                                let pts_init = remove_last pts in
                                let tp = gen_type_arg lenFinSeq lower upper libName funcName type_class_tbl type_tbl field_tbl inst_tbl pattern_tbl pt_last nth ith in
                                let indexList = init_list (pt_num - 1) in
                                let argList = List.map (fun i -> "x" ^ (string_of_int (i + 1))) indexList in
                                let ml_arg = "fun " ^ (String.concat " " argList) ^ " -> " ^ (fst tp) in
                                let pvs_arg = "LAMBDA" ^ (String.concat "" (List.map2 (fun x pt -> "(" ^ x ^ ": " ^ (string_of_typename lenFinSeq pt) ^ ")") argList pts_init)) ^ ": " ^ (snd tp) in
                                (ml_arg, pvs_arg)
                              end
                          end
                        else
                          begin
                            let ptNum = List.length patList in
                            let key = Random.int ptNum in
                            let pvs_name = List.nth patList key in
                            let ml_name = map_func_pvs_ml pvs_name pts in
                            if ml_name = "" then
                              printf "undefined ml function in map_func_pvs_ml: pvs name: %s\n" pvs_name;
                            (ml_name, pvs_name)
                          end
                      with Not_found -> begin
                          let patName = string_of_typename lenFinSeq curType in
                          (* printf "Undefined behavior for the function pattern_not_found: %s\n" patName; *)
                          let pt_num = List.length pts in
                          let pt_last = List.nth pts (pt_num - 1) in
                          let pts_init = remove_last pts in
                          let tp = gen_type_arg lenFinSeq lower upper libName funcName type_class_tbl type_tbl field_tbl inst_tbl pattern_tbl pt_last nth ith in
                          let indexList = init_list (pt_num - 1) in
                          let argList = List.map (fun i -> "x" ^ (string_of_int (i + 1))) indexList in
                          let ml_arg = "fun " ^ (String.concat " " argList) ^ " -> " ^ (fst tp) in
                          let pvs_arg = "LAMBDA" ^ (String.concat "" (List.map2 (fun x pt -> "(" ^ x ^ ": " ^ (string_of_typename lenFinSeq pt) ^ ")") argList pts_init)) ^ ": " ^ (snd tp) in
                          (ml_arg, pvs_arg)
                        end
                    end
                 | PType (name, pt1, pt2) -> begin match pt1 with
                                             | PEmpty -> (name, name)
                                             | _ -> begin match pt2 with
                                                    | PSpec ps -> begin match ps with
                                                                  | PNVar nv -> begin
                                                                      let compName = libName ^ "@" ^ name in
                                                                      let tDefs = Hashtbl.find type_tbl compName in
                                                                      let args = gen_type_arg lenFinSeq lower upper libName funcName type_class_tbl type_tbl field_tbl inst_tbl pattern_tbl pt1 nth ith in
                                                                      args
                                                                    end
                                                                  end
                                                    end
                                            end
                 | _ -> failwith ("gen_type_arg: undefined behavior for the type " ^ (string_of_typename 0 curType)))

       
let get_ml_func_name funcName = funcName

let rec auxiliary_info libName tp = match tp with
  | PComplex pc -> (match pc with
                    | PList tp -> let aux = auxiliary_info libName tp in
                                  if fst aux then
                                    (true, "List.map (" ^ (snd aux) ^ ")")
                                  else
                                    (false, "")
                    | PTuple tps -> let auxs = List.map (auxiliary_info libName) tps in
                                    let need_aux = (List.length (List.filter (fun x -> fst x = true) auxs)) > 0 in
                                    if need_aux then
                                      begin
                                        let len = List.length tps in
                                        let indexes = init_list len in
                                        let elems = String.concat ", " (List.map (fun i -> "x" ^ (string_of_int (i + 1))) indexes) in
                                        let applies = String.concat ", " (List.map2 (fun i x -> "(" ^ (snd x) ^ ") x" ^ (string_of_int (i + 1))) indexes auxs) in
                                        let info = "(fun temp -> let (" ^ elems ^ ") = temp in (" ^ applies ^ "))" in
                                        (true, info)
                                      end
                                    else
                                      (false, "")
                    | _ -> (false, ""))
  | PDef pd -> (match pd with
                | PBit -> (true, string_of_vbit)
                | PBvec -> (true, string_of_value)
                | PRat -> (true, string_of_rat)
                | _ -> (false, ""))
  | PExt pe -> let string_of_bigint = snd (List.find (fun x -> fst x = libName) string_of_big_int) in
               (match pe with
                | PBigInt -> (true, string_of_bigint)
                | PBigNat -> (true, string_of_bigint)
                | PInt32 -> (true, "Int32.to_string")
                | PInt64 -> (true, "Int64.to_string"))
  | _ -> (false, "")
       
(* Generate the nth argument of a function *)   
let gen_nth_arg libName funcName nth typeNum typeList lenFinSeq lower upper type_class_tbl type_tbl field_tbl inst_tbl pattern_tbl tv_list =
  let _ = inst_type_variable tv_list in
  let mlArgList = ref [] in
  let pvsArgList = ref [] in
  for i = 0 to typeNum - 2 do
    let curType = replace_type_variable tv_tbl (List.nth typeList i) in
    (* printf "gen_nth_arg %s %s %d %s\n" libName funcName nth (string_of_typename lenFinSeq curType); *)
    let (mlArg, pvsArg) = gen_type_arg lenFinSeq lower upper libName funcName type_class_tbl type_tbl field_tbl inst_tbl pattern_tbl curType nth i in
    mlArgList := !mlArgList @ [mlArg];
    pvsArgList := !pvsArgList @ [pvsArg];
  done;
  let returnType = List.nth typeList (typeNum - 1) in
  let extraTransfer, extraInfo = auxiliary_info libName returnType in
  let mlArgs = string_of_ml_args !mlArgList in
  let pvsArgs = string_of_pvs_args !pvsArgList in
  (mlArgs, pvsArgs, extraTransfer, extraInfo)


(* Parse the executed ml function result to string in .pvs format *)
let rec parseResult lenFinSeq field_tbl libName resultType obj =
  let curType = replace_type_variable tv_tbl resultType in
  match curType with
  | PBasic pb -> (match pb with
                  | PUnit -> ("unit", 0)
                  | PBool -> (string_of_bool ((Obj.magic obj) : bool), 0)
                  | PChar -> let str = Char.escaped ((Obj.magic obj) : char) in
                             if str = "\"" then
                               (str, 0)
                             else
                               ("\"" ^ str ^ "\"(0)", 0)
                  | PNat -> (string_of_int ((Obj.magic obj) : int), 0)
                  | PInt -> (string_of_int ((Obj.magic obj) : int), 0)
                  | PReal -> (string_of_float ((Obj.magic obj) : float), 0)         
                 )
  | PComplex pc -> (match pc with
                    | PString -> let result = ((Obj.magic obj) : string) in
                                 let ret = if contains result "\\" then -1 else 0 in
                                 if contains result "\"" then
                                   let strs = full_split "\"" result in
                                   let new_strs = List.map (fun s -> if s = "\"" then "doublequote" else "\"" ^ s ^ "\"") strs in
                                   let strResult = List.fold_right (fun x y -> if y = "\"\"" then x
                                                                               else x ^ " o  (" ^ y ^ ")") new_strs "\"\"" in
                                   (strResult, ret)
                                 else
                                   ("\"" ^  result ^ "\"", ret)
                    | PList tp -> let xs = ((Obj.magic obj) : 'a list) in
                                  let ys = List.map (fun x -> parseResult lenFinSeq field_tbl libName tp (Obj.repr x)) xs in
                                  let strResult = if List.length ys == 0 then "null[" ^ (string_of_typename lenFinSeq tp) ^ "]"
                                                  else "(: " ^ (String.concat ", " (List.map (fun x -> fst x) ys)) ^ " :)" in
                                  let failed = List.length (List.filter (fun x -> snd x == -1) ys) > 0 in
                                  if failed then
                                    (strResult, -1)
                                  else
                                    (strResult, 0)
                    | PTuple pts -> let len = List.length pts in
                                    let indexList = init_list len in
                                    let xs = List.map (fun i -> parseResult lenFinSeq field_tbl libName (List.nth pts i) (Obj.field obj i)) indexList in
                                    ("(" ^ (String.concat ", " (List.map fst xs)) ^ ")", List.fold_left (+) 0 (List.map snd xs))
                   )
  | PDef pd -> (match pd with
                | PBit -> let result = ((Obj.magic obj) : string) in
                          if result = "u" then
                            (result, -1)
                          else
                            (bit_of_intstring result, 0)
                          
                | PBvec -> let result = ((Obj.magic obj) : string) in
                           if contains result "inc" && not (contains result "reg") then
                             let bitArr = get_split_elem "inc" result 1 in
                             if contains bitArr "u" then (result, -1)
                             else
                               let strResult = string_of_vec (bit_arr_of_string bitArr) in
                               (strResult, 0)
                           else if contains result "dec" && not (contains result "reg") then
                             let bitArr = get_split_elem "dec" result 1 in
                             if contains bitArr "u" then (result, -1)
                             else
                               let strResult = string_of_vec (bit_arr_of_string bitArr) in
                               (strResult, 0)
                           else
                             (result, -1)
                           
                | PRat -> let result = ((Obj.magic obj) : string) in
                          if contains result "inf" then (result, -1)
                          else (result, 0)
                | PSet pt -> let tp = string_of_typename lenFinSeq pt in
                             let st = ((Obj.magic obj) : 'a set) in
                             let result = set_fold (fun x y -> let (s, ret) = parseResult lenFinSeq field_tbl libName pt x in
                                                               let str = "x = " ^ s in
                                                               if (fst y) = "" then
                                                                 (str, ret + snd y)
                                                               else
                                                                 (str ^ " OR " ^ fst y, ret + snd y)) st ("", 0) in
                             if (fst result = "") then
                               ("emptyset[" ^ (string_of_typename lenFinSeq pt) ^ "]", snd result)
                             else
                               ("{x : " ^ tp ^ " | " ^ fst result ^ "}", snd result)
                | PDataType (name, pt) -> let fields = Hashtbl.find field_tbl (libName ^ "@" ^ name) in
                                          let field_tvs = unique (List.flatten (List.map list_of_type_variables fields)) in
                                          let field_tv_tbl = Hashtbl.create 10 in
                                          let _ = if List.length field_tvs > 1 then
                                                    let _ = match pt with
                                                      | PComplex (PTuple tps) -> List.iter2 (fun x y -> Hashtbl.add field_tv_tbl x y) field_tvs tps
                                                      | _ -> failwith ("gen_type_arg: the number of type varialbes for datatype " ^ name ^ " does not match the size of the parsed type") in
                                                    ()
                                                  else
                                                    List.iter (fun x -> Hashtbl.add field_tv_tbl x pt) field_tvs in
                                          let fields = List.map (replace_type_variable field_tv_tbl) fields in
                                          let result = ref "" in
                                          let out = ref 0 in
                                          if Obj.is_block obj then
                                            begin
                                              let arg_fields = List.filter (fun s -> match s with
                                                                                     | PDef (PField (field_name, field_pt)) -> field_pt != PEmpty
                                                                                     | _ -> false) fields in
                                              let selected_field = List.nth arg_fields (Obj.tag obj) in
                                              let field_name, field_pt = match selected_field with
                                                | PDef (PField (field_name, field_pt)) -> (field_name, field_pt)
                                                | _ -> ("", PEmpty) in
                                              result := field_name ^ "(";
                                              let obj_size = Obj.size obj in
                                              if obj_size == 1 then
                                                begin
                                                  let field_tp, res = parseResult lenFinSeq field_tbl libName field_pt (Obj.repr (Obj.field obj 0)) in
                                                  result := !result ^ field_tp ^ ")";
                                                  out := !out + res
                                                end
                                              else
                                                begin
                                                  let field_list = match field_pt with
                                                    | PComplex (PTuple pts) -> pts in
                                                  let obj_init_list = init_list obj_size in
                                                  result := !result ^ (String.concat ", " (List.map (fun i -> let field_tp, res = parseResult lenFinSeq field_tbl libName (List.nth field_list i) (Obj.repr (Obj.field obj i)) in
                                                                                                              out := !out + res;
                                                                                                              field_tp) obj_init_list)) ^ ")"
                                                end
                                            end
                                          else
                                            begin
                                              let no_arg_fields = List.filter (fun s -> match s with
                                                                                        | PDef (PField (field_name, field_pt)) -> field_pt = PEmpty
                                                                                        | _ -> false) fields in
                                              let idx = ((Obj.magic obj): int) in
                                              let selected_field = List.nth no_arg_fields idx in
                                              let field_name = match selected_field with
                                                | PDef (PField (field_name, PEmpty)) -> field_name
                                                | _ -> "" in
                                              result := field_name;
                                            end;
                                          (!result, !out)
                | PRecord (name, pt) -> begin
                    printf "parseResult: undefined behavior for the type %s\n" (string_of_typename lenFinSeq curType);
                    ("", -1)                             
                  end)
  | PExt pe -> (match pe with
                | PBigInt -> (((Obj.magic obj) : string), 0)
                | PBigNat -> (((Obj.magic obj) : string), 0)
                | PInt32 -> (((Obj.magic obj) : string), 0)
                | PInt64 -> (((Obj.magic obj) : string), 0))
  | PSpec ps -> (match ps with 
                 | PType (name, pt1, pt2) -> parseResult lenFinSeq field_tbl libName pt1 obj
                 | _ -> failwith ("parseResult: undefined behavior for the type " ^ string_of_typename lenFinSeq curType))
  | PEmpty -> failwith ("parseResult: undefined behavior for the type PEmpty")