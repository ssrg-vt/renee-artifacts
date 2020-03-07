#!/bin/bash
echo "Bash version ${BASH_VERSION}..."
for i in {0..999..1}
  do 
    python test_lemma_generator_pvs.py adr.xml adr
 done
