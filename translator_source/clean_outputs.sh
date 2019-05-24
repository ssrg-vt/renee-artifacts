#!/bin/bash
json_dir="/assets/intermediate_json_files/"
dec_dir="/assets/intermediate_dec_files/"
pvs_dir="/output_pvs_files/"
path=$PWD$json_dir
cd "${path}"
rm *.*
echo "/intermediate_json_files .. all files deleted"
cd ../..
path2=$PWD$dec_dir
cd "${path2}"
rm *.*
echo "/intermediate_dec_files .. all files deleted"
cd ../..
path3=$PWD$pvs_dir
cd "${path3}"
rm *.*
echo "/output_pvs_files .. all files deleted"
cd ..
