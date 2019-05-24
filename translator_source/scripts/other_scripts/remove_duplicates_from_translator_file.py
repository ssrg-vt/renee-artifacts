# This code helps to translate the zircon.txt file to dict.txt file

import re
import sys

with open (sys.argv[1]) as f:
  content = f.readlines()
content = [x.strip() for x in content]
inst_class_map = {}
for x in content:
    print x
    pair = re.split("\s+",x)
    class_name = pair[0]
    inst_name = pair[1]
    if inst_name in inst_class_map:
        continue
    else:
        inst_class_map[inst_name] = class_name
print "*****************"
f = open("dict.txt","w")
for key, value in inst_class_map.iteritems():
    f.write (value + "\t " + key+ "\n")
