#!/bin/bash
# This script accepts input from the txt file with the format <<condbranch	b_cond.xml>> for each line. <<classname>> <<inst.xml>>

while IFS='' read -r line || [[ -n "$line" ]]; do
   echo "Parsing xml file for the class - inst pair :$line"
   python auto_translator_ASL_inst.py  "$line"
   
done < "$1"

#echo "Enter path to PVS"
#read pvspath
#find . -maxdepth 1 -name '*.pvs' -mmin -5500 -exec cp -v '{}' "$pvspath" \;
