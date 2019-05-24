#!/bin/bash
echo "Bash version ${BASH_VERSION}..."
for i in {0..65..1}
  do 
    python test_lemma_generator_pvs.py eor_log_shift.xml eor_log
 done
