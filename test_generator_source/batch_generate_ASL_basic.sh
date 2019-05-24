#!/bin/bash
# This file analyzes the xml files for some defined patterns by calling the util script

while IFS='' read -r line || [[ -n "$line" ]]; do
   #echo "Parsing xml file for the class - inst pair :$line"
   python auto_translator_ASL_basic.py  "$line"
done < "$1"

#echo "Enter path to PVS"
#read pvspath
#find . -maxdepth 1 -name '*.pvs' -mmin -5500 -exec cp -v '{}' "$pvspath" \;
