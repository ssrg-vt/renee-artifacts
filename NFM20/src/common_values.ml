open Topdirs
open Toploop
open Unix
open Thread
open Str
open Yojson.Basic.Util
open Printf
open Utils
open Lib_spec
open Pretty_print
open Type_spec

let jsonFile = "data.json"

let testCaseDir = ref ""
let testFileName = ref ""
let proveitPath = ref ""

let libNames = ref ""

let pid = int_of_string(String.trim (syscall "pgrep opev"))

let pvs_lib_list = ref []
let func_name_tbl = Hashtbl.create 2

let func_type_tbl = Hashtbl.create 10
let theory_name_tbl = Hashtbl.create 10

let type_tbl = Hashtbl.create 10
let type_class_tbl = Hashtbl.create 10

let const_tbl = Hashtbl.create 10
let field_tbl = Hashtbl.create 10
let inst_tbl = Hashtbl.create 10

let pattern_tbl = Hashtbl.create 10

let queue = Queue.create ()
let mutex = Mutex.create ()

let proveResult = ref ""
let proveMutex = Mutex.create ()


let initialize_toplevel =
  Toploop.initialize_toplevel_env ();
  Topdirs.dir_directory (Sys.getenv "OCAML_TOPLEVEL_PATH");
  eval "#use \"topfind\";;"

let _ =
  let _ = initialize_toplevel in
  let json = Yojson.Basic.from_file jsonFile in
  let tags = List.map json_to_string (json |> member "tags" |> json_to_list) in
  testCaseDir := json |> member (List.nth tags 0) |> json_to_string;
  proveitPath := json |> member (List.nth tags 1) |> json_to_string;
  let pvsLibs = json |> member (List.nth tags 2) |> json_to_list in
  pvs_lib_list := List.map (json_to_string) pvsLibs;
  libNames := String.concat "," !pvs_lib_list;
  let libNum = List.length pvsLibs in
  for n = 0 to libNum - 1 do
    let libName = List.nth !pvs_lib_list n in
    (* printf "index = %d, libName: %s\n" n libName; *)
    let libData = json |> member libName in
    let mlSrcFiles = libData |> member (List.nth tags 3) |> json_to_list in
    let ext_lib_cmds = libData |> member (List.nth tags 4) |> json_to_list in
    let ext_mls = libData |> member (List.nth tags 5) |> json_to_list in
    let ext_lib_num = List.length ext_lib_cmds in
    for i = 0 to ext_lib_num - 1 do
      let ext_lib_cmd = json_to_string (List.nth ext_lib_cmds i) in
      printf "%s\n" ext_lib_cmd;
      eval ext_lib_cmd
    done;
    let ext_mls_num = List.length ext_mls in
    for i = 0 to ext_mls_num - 1 do
      let ext_mls_cmd = json_to_string (List.nth ext_mls i) in
      printf "%s\n" ext_mls_cmd;
      eval ext_mls_cmd
    done;
    let mlSrcNum = List.length mlSrcFiles in
    for i = 0 to mlSrcNum - 1 do
      let cmd = sprintf "#mod_use \"%s\";;" (json_to_string (List.nth mlSrcFiles i)) in
      printf "%s\n" cmd;
      eval cmd
    done;
    let functionList = libData |> member (List.nth tags 6) |> json_to_assoc in
    let constList = libData |> member (List.nth tags 7) |> json_to_assoc in
    let typeList = libData |> member (List.nth tags 8) |> json_to_assoc in
    let instList = libData |> member (List.nth tags 9) |> json_to_assoc in
    let patternList = libData |> member (List.nth tags 10) |> json_to_assoc in
    let typeNum = List.length typeList in
    for i = 0 to typeNum - 1 do
      let typeInfo = List.nth typeList i in
      let typeName = fst typeInfo in
      let compName = libName ^ "@" ^ typeName in
      let typeDecs = List.map (json_to_string) (snd typeInfo |> json_to_list) in
      let tType = List.nth typeDecs 0 in
      let tDefs = Utils.split ":" (List.nth typeDecs 1) in
      (* printf "User-defined type: %s %s %s\n" compName tType (List.nth typeDecs 1); *)
      Hashtbl.add type_class_tbl compName tType;
      Hashtbl.add type_tbl compName tDefs
    done;
    for i = 0 to typeNum - 1 do
      let typeInfo = List.nth typeList i in
      let typeName = fst typeInfo in
      let typeDecs = List.map (json_to_string) (snd typeInfo |> json_to_list) in
      let tType = List.nth typeDecs 0 in
      if String.equal tType "datatype" || String.equal tType "record"  then
        begin
          let tDefs = Utils.split ";" (List.nth typeDecs 1) in
          let fType = List.map (fun s -> let fs = Str.bounded_split (Str.regexp ":") (String.trim s) 2 in
                                       if List.length fs > 1 then
                                         PDef (PField (List.nth fs 0, (parseFuncType type_class_tbl type_tbl libName "" (List.nth fs 1))))
                                       else
                                         PDef (PField (List.nth fs 0, PEmpty))) tDefs in
          Hashtbl.add field_tbl (libName ^ "@" ^ typeName) fType
        end
    done;
    let instNum = List.length instList in
    for i = 0 to instNum - 1 do
      let instInfo = List.nth instList i in
      let recordName = fst instInfo in
      let insts = List.map json_to_string (snd instInfo |> json_to_list) in
      let inst_list = List.map (fun s -> let ss = split ":" s in
                                         let ss_split = split "." (List.nth ss 1) in
                                         (* printf "inst_table: original: %s, type: %s, libName: %s, instName: %s\n" s (List.nth ss 0) (List.nth ss_split 0) (List.nth ss_split 1); *)
                                         (List.nth ss 0, List.nth ss_split 0, List.nth ss_split 1)) insts in
      Hashtbl.add inst_tbl (libName ^ "@" ^ recordName) inst_list
    done;
    let funcNum = List.length functionList in
    let funcNames = String.concat "," (List.map fst functionList) in
    for i = 0 to funcNum - 1 do
      let funcInfo = List.nth functionList i in
      let funcName = fst funcInfo in
      let typeInfo = List.map (json_to_string) (snd funcInfo |> json_to_list) in
      let funcType = List.nth typeInfo 0 in
      let theoryName = List.nth typeInfo 1 in
      (* printf "funcName: %s, funcType: %s, theoryName: %s\n" funcName funcType theoryName; *)
      Hashtbl.add func_type_tbl (libName ^ "@" ^ funcName) funcType;
      Hashtbl.add theory_name_tbl (libName ^ "@" ^ funcName) (libName ^ "@" ^ theoryName)
    done;
    let constNum = List.length constList in
    for i = 0 to constNum - 1 do
      let constInfo = List.nth constList i in
      let theoryName = fst constInfo in
      let constDecs = snd constInfo |> json_to_assoc in
      let constPair = List.map (fun (name, ctp) -> let tp = parseFuncType type_class_tbl type_tbl libName "" (ctp |> json_to_string) in
                                                   (name, tp)) constDecs in
      Hashtbl.add const_tbl (libName ^ "@" ^ theoryName) constPair
    done;
    let patternNum = List.length patternList in
    for i = 0 to patternNum - 1 do
      let patternInfo = List.nth patternList i in
      let patternType = fst patternInfo in
      let patternName = parseFuncType type_class_tbl type_tbl libName "" patternType in
      let patternDecs = List.map (json_to_string) (snd patternInfo |> json_to_list) in
      Hashtbl.add pattern_tbl (libName, patternName) patternDecs
    done;
    Hashtbl.add func_name_tbl libName funcNames
  done

let gen_file_name funcName maxTestNum =
  let curTime = Unix.localtime (Unix.time ()) in
  let timeStamp = sprintf "%d_%d_%d_%d_%d_%d" (curTime.tm_year + 1900) (curTime.tm_mon + 1) curTime.tm_mday curTime.tm_hour curTime.tm_min curTime.tm_sec in
  let filename = ref "" in
  if String.equal funcName "" then
    filename := sprintf "test_%d_%s" maxTestNum timeStamp
  else
    filename := sprintf "test_%s_%d_%s" funcName maxTestNum timeStamp;
  !filename


let gen_exec_result libName funcName lenFinSeq lower upper maxTestNum =
  let realName = List.nth (Str.split (Str.regexp "\.") funcName) 1 in
  let comboName = libName ^ "@" ^ funcName in
  let printResult = ref "" in
  let funcTypes = Hashtbl.find func_type_tbl comboName in
  let theoryName = Hashtbl.find theory_name_tbl comboName in
  printResult := sprintf "%sIMPORTING %s\n\n" !printResult theoryName;
  let tpCmd = sprintf "%s;;" funcName in
  let out, res = eval_type tpCmd in
  printf "%s  %s  %d\n" tpCmd out res;
  let realFuncType = if res == 0 then
                       get_split_elem "=" (get_split_elem ":" out 1) 0
                     else
                       "" in
  let pvsArgList = parseStringBK funcTypes "[" "]" "->" in
  let mlArgList = List.map (String.trim) (parseStringBK realFuncType "(" ")" "->") in
  let pvsArgNum = List.length pvsArgList in
  let mlArgNum = List.length mlArgList in
  (* printf "combName: %s   funcTypes: %s   realFuncType: %s   pvsArgNum: %d    mlArgNum:%d\n" comboName funcTypes realFuncType pvsArgNum mlArgNum; *)
  Random.self_init ();
  if mlArgNum == pvsArgNum then
    begin
      let typeList = List.map2 (parseFuncType type_class_tbl type_tbl libName) mlArgList pvsArgList in
      let tvar_list = unique (List.flatten (List.map list_of_type_variables typeList)) in
      let typeNum = List.length typeList in
      let resultType = List.nth typeList (typeNum - 1) in
      for ith = 0 to maxTestNum - 1 do
        let (mlArgs, pvsArgs, extraTransfer, extraInfo) = gen_nth_arg libName realName ith typeNum typeList lenFinSeq lower upper type_class_tbl type_tbl field_tbl inst_tbl pattern_tbl tvar_list in
        let mlFuncName = get_ml_func_name funcName in
        let mlCmd = if not extraTransfer then
                      sprintf "let result = %s %s;;" mlFuncName mlArgs
                    else
                      sprintf "let result = %s (%s %s);;" extraInfo mlFuncName mlArgs in
        (* printf "%s\n" mlCmd; *)
        let out, res = eval mlCmd in
        if res == 0 then
          begin
            let (result, status) = parseResult lenFinSeq field_tbl libName resultType (Toploop.getvalue "result") in
            if status == 0 then
              begin
                (* printf "%s\nth_%s_%d: LEMMA %s%s = %s\n\n" !printResult realName ith realName pvsArgs result; *)
                printResult := sprintf "%s\nth_%s_%d: LEMMA %s%s = %s\n\n" !printResult realName ith realName pvsArgs result
              end
            (* else
             *   printf "parseResult wrong: %s\n" mlCmd; *)
          end
        (* else
         *   printf "res = %d, %s\n" res mlCmd; *)
      done;
      let pvsStrategy = snd (List.find (fun x -> fst x = libName) pvsStrategies) in
      printResult := sprintf "%s\n%%|- th_%s_*: PROOF (%s) QED\n\n\n" !printResult realName pvsStrategy
    end;
  !printResult


let generate funcNames lenFinSeq lower upper maxTestNum =
  let fileName = gen_file_name "" maxTestNum in
  testFileName := fileName;
  let printResult = ref fileName in
  printResult := !printResult ^ " : THEORY\nBEGIN\n\n";
  let funcNameLists = Str.split (Str.regexp ",") funcNames in
  let funcNum = List.length funcNameLists in
  for n = 0 to funcNum - 1 do
    let funcName_combine = Utils.split ":" (List.nth funcNameLists n) in
    let libName = List.nth funcName_combine 0 in
    let funcName = List.nth funcName_combine 1 in
    let result = gen_exec_result libName funcName lenFinSeq lower upper maxTestNum in
    printResult := sprintf "%s\n%s" !printResult result
  done;
  printResult := !printResult ^ "\nEND " ^ fileName;
  let filePath = sprintf "%s/%s.pvs" !testCaseDir fileName in
  let file = open_out filePath in
  fprintf file "%s" !printResult;
  close_out file;
  !printResult


let generate_all libName lenFinSeq lower upper maxTestNum =
  let funcNames = Hashtbl.find func_name_tbl libName in
  let funcNameLists = Str.split (Str.regexp ",") funcNames in
  let funcNum = List.length funcNameLists in
  let allFileNames = ref "" in
  for n = 0 to funcNum - 1 do
    let funcName = List.nth funcNameLists n in
    print_endline funcName;
    let realName = List.nth (Str.split (Str.regexp "\.") funcName) 1 in
    let fileName = gen_file_name realName maxTestNum in
    allFileNames := !allFileNames ^ fileName ^ ".pvs\n\n";
    let printResult = ref fileName in
    printResult := !printResult ^ " : THEORY\nBEGIN\n\n";
    let result = gen_exec_result libName funcName lenFinSeq lower upper maxTestNum in
    printResult := sprintf "%s\n%s" !printResult result;
    printResult := !printResult ^ "\nEND " ^ fileName;
    let filePath = sprintf "%s/%s.pvs" !testCaseDir fileName in
    let file = open_out filePath in
    fprintf file "%s" !printResult;
    close_out file;
    Queue.push fileName queue;
  done;
  !allFileNames

let max_thread_num = int_of_string(String.trim (syscall "grep -c ^processor /proc/cpuinfo"))
let total_memory = int_of_string(String.trim (syscall "free | grep Mem | awk '{print $2}'"))
let running_thread_num = ref max_thread_num

let get_curr_mmu_str = "free | grep Mem | awk '{print $3}'"
let get_proc_mmu_str = sprintf "echo 0 $(awk '/Rss/ {print \"+\", $2}' /proc/%d/smaps) | bc" pid


let basic_mmu = ref (int_of_string(String.trim (syscall get_curr_mmu_str)))

let threshold_mmu = int_of_float(float_of_int(total_memory) *. 0.9)
let safe_mmu = ref ((threshold_mmu + !basic_mmu) / 2)
let balancing_mmu = ref ((threshold_mmu + !safe_mmu) / 2)


let update_mmu_value () =
  let out = String.trim (syscall get_proc_mmu_str) in
  let cur_mmu = int_of_string(out) in
  let new_basic_mmu = int_of_string(String.trim (syscall get_curr_mmu_str)) - cur_mmu in
  basic_mmu := new_basic_mmu;
  safe_mmu := (threshold_mmu + new_basic_mmu) / 2;
  balancing_mmu := (threshold_mmu + !safe_mmu) / 2;
  ()

let threads = ref []
let thread_status = Array.make max_thread_num true

let append_prove_result result =
  Mutex.lock proveMutex;
  proveResult := sprintf "%s\n-----------------------------------------------\n\n%s\n" !proveResult result;
  Mutex.unlock proveMutex;
  ()

let prove () =
  let fileName = !testFileName in
  print_endline fileName;
  print_endline !testCaseDir;
  let testName = sprintf "%s/%s.pvs" !testCaseDir fileName in
  let cmd = sprintf "%s %s" !proveitPath testName in
  print_endline cmd;
  let result = ref "" in
  let status = Unix.system cmd in
  let out = check_exit_status status in
  let sumName = sprintf "%s/%s.summary" !testCaseDir fileName in
  if out == 0 then
      result := load_file sumName;
  !result

let thread_prove () =
  let tid = Thread.id (Thread.self ()) in
  let idx = tid mod max_thread_num in
  (* Array.set thread_status idx true; *)
  (try
     while true do
       if (Array.get thread_status idx) then
         begin
           Mutex.lock mutex;
           let fileName = Queue.pop queue in
           Mutex.unlock mutex;
           let testName = sprintf "%s/%s.pvs" !testCaseDir fileName in
           let cmd = sprintf "%s %s" !proveitPath testName in
           let out = syscall cmd in
           append_prove_result out
         end
       else
         Unix.sleep 5
    done
   with empty -> ());
  ()

let set_thread_status num =
  Array.fill thread_status 0 num true;
  Array.fill thread_status num (max_thread_num - num) false;
  running_thread_num := num;
  ()

let max_iter_count = 10
let cur_iter_count = ref 0

let monitor () =
  while not (Queue.is_empty queue) do
    let mmu = int_of_string(String.trim (syscall get_curr_mmu_str)) in
    if !cur_iter_count == max_iter_count then
      begin
        update_mmu_value ();
        cur_iter_count := 0
      end
    else
      cur_iter_count := !cur_iter_count + 1;
    if mmu > threshold_mmu then
        set_thread_status 1
    else if mmu <= !safe_mmu then
      begin
        let thread_mmu = (float_of_int(mmu - !basic_mmu)) /. (float_of_int(!running_thread_num)) in
        let thread_num = int_of_float(float_of_int(!balancing_mmu - !basic_mmu) /. thread_mmu) in
        let new_thread_num = if thread_num <= max_thread_num then thread_num else max_thread_num in
        set_thread_status new_thread_num
      end;
    Unix.sleep 5
  done;
  set_thread_status max_thread_num;
  ()

let prove_all () =
  proveResult := "";
  set_thread_status 1;
  for i = 0 to max_thread_num - 1 do
    let thread = Thread.create thread_prove () in
    threads := !threads @ [thread]
  done;
  let monitor_thread = Thread.create monitor () in
  for i = 0 to max_thread_num - 1 do
    let thread = List.nth !threads i in
    Thread.join thread
  done;
  Thread.join monitor_thread;
  proveResult := sprintf "%s\n-----------------------------------------------\n\n%s\n" !proveResult "There are no further test cases to prove!";
  printf "%s" !proveResult;
  !proveResult
