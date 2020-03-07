open Printf
open Utils
open Common_values

(* exemple.ml *)

let verbose = ref false
let to_validate = ref false

let max_seq_length = ref 8
let lower_bound = ref (-10)
let upper_bound = ref 10
let num_test_cases = ref 10

let validate name = 
  begin
    let print_result = ref "" in
    let proof_summary = ref "" in
    if Utils.endswith ".pvs" name then
      begin
        print_result := Common_values.generate name !max_seq_length !lower_bound !upper_bound !num_test_cases;
        proof_summary := if !to_validate then (Common_values.prove ()) else ""
      end
    else
      begin
        print_result := Common_values.generate_all name !max_seq_length !lower_bound !upper_bound !num_test_cases;
        proof_summary := if !to_validate then (Common_values.prove_all ()) else ""
      end;
    if !verbose then
      begin
        print_endline !print_result;
        print_endline !proof_summary
      end
    else
      ()
  end

let main =
  begin
    let speclist = [("--verbose", Arg.Set verbose, "Enables verbose mode");
                    ("--length", Arg.Set_int max_seq_length, "Sets maximum length of sequences");
                    ("--number", Arg.Set_int num_test_cases, "Sets maximum number of generated test cases");
                    ("--range", Arg.Tuple ([Arg.Set_int lower_bound; Arg.Set_int upper_bound]), "Set the lower and upper bound for integer and natural number random generation");
                    ("--validate", Arg.Set to_validate, "Validate the generated test cases");
                    ] in
    let usage_msg = "OPEV can be used to validate the conformance relathionship between translated PVS and OCaml specifications. Available Options include:" in
    Arg.parse speclist validate usage_msg
  end
          
let () = main
