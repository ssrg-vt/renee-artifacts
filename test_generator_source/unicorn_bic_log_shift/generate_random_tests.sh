#!/bin/bash
echo "Bash version ${BASH_VERSION}..."
for i in {0..65..1}
  do 
    python test_lemma_generator_pvs.py bic_log_shift.xml bic_log
 done
