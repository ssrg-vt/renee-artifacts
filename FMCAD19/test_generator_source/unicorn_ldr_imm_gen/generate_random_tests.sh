#!/bin/bash
echo "Bash version ${BASH_VERSION}..."
for i in {0..20..1}
  do 
    python test_lemma_generator_pvs.py ldr_imm_gen.xml ldr
 done
