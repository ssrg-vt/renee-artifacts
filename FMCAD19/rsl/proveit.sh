#!/bin/bash
while IFS='' read -r line || [[ -n "$line" ]]; do
    ./proveit -force "$line"
   echo "$line"
done < "$1"
