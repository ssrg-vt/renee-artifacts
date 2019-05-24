#!/bin/bash
echo "Bash version ${BASH_VERSION}..."
for i in {0..19..1}
  do 
     python test_lemma_generator_pvs.py subs_addsub_imm.xml addsub_imm
 done
