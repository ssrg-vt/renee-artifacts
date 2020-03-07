import re

classes = {}
f = open ("classes_get_class.txt", "r")
for line in f:
	line = line.strip()
	tokens = re.split("\s+", line)
	inst_name = tokens [0]
        class_name = tokens [1]
	if class_name in classes:
		inst_dict = classes[class_name]
                if inst_name not in inst_dict:
			inst_dict.append (inst_name)
	else:
		temp = []
		temp.append (inst_name)
		classes[class_name] = temp


for key, value in classes.iteritems():
	print str(key) +  "::" + str(value)

for name in classes:
	print name
