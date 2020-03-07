#!/bin/bash
while IFS='' read -r line || [[ -n "$line" ]]; do
    proveit  "$line"
   echo "$line"
done < "$1"
