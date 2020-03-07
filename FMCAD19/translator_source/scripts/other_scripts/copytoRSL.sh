#!/bin/bash
echo Please enter the filename to generate .pvs files
read output_path
input_folder="/output_pvs_files/"
path=$PWD$input_folder
echo $path
timestamp=$(date +"%Y%m%d-%H%M%S")
output_fname="batch_"
cd "${path}"
ls *.pvs > $output_fname$timestamp
cp $path* $output_path 
echo "All psv files copied from output_pvs_folder to RSL dir file copied!"

