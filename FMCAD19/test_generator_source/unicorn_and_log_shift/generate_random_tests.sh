#!/bin/bash
echo "Bash version ${BASH_VERSION}..."
for i in {0..299..1}
  do
    python test_lemma_generator_pvs.py and_log_shift.xml and_log
 done
