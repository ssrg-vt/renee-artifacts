#!/bin/bash
echo "Bash version ${BASH_VERSION}..."
for i in {0..25..1}
  do 
    python test_lemma_generator_pvs.py ldrb_imm.xml ldr
 done
