#!/bin/bash
echo "Bash version ${BASH_VERSION}..."
for i in {0..100..1}
  do 
    python test_lemma_generator_pvs.py str_imm_gen.xml str
 done
