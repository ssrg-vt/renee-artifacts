#!/bin/bash
echo Please enter the filename to generate .pvs files
read filename
echo Please enter --linux for linux and --zircon for zircon
read target
r2_ext=".r2"
term_ext=".term"
batch_ext=".batch"
bdec_ext=".batch_dec"
#echo Running script to find terminal functions 
#python terminal_fn_finder_recursive_radare2.py  "$filename$r2_ext"
echo Running script to generate json files 
python json_generator_radare2.py  "$filename$term_ext" "$target"
echo Running script for loop discovery and generating paths json_parser_radare2.py
python json_parser_radare2.py  "$filename$batch_ext"
echo Running script to decode .dec files auto_decoder.py
python auto_decoder.py  "$filename$bdec_ext"
#echo Please enter the path to copy the generated pvs files to
#read output_path
#input_folder="/output_pvs_files/"
#path=$PWD$input_folder
#echo $path
#timestamp=$(date +"%Y%m%d-%H%M%S")
#output_fname="batch_"
#cd "${path}"
#ls *.pvs > $output_fname$timestamp
#cp $path* $output_path 
#echo "All psv files copied from output_pvs_folder to RSL dir file copied!"


