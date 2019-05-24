import re

classes = {}
fn_list = []
fnc_name = ""
cnt = 0
f = open ("analysis2", "r")
for line in f:
	line = line.strip()
	tokens = re.split("\s+", line)
        if len(tokens) == 2:
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
	else:			
		print str (classes)  # the dictionary of classes of instructions and the corresponding insts
		classes = {}
		if not fnc_name == tokens [0].rsplit('_',1)[0]:
			fnc_name = tokens [0].rsplit('_',1)[0]
			print "\n\n\n********* Function name::" + fnc_name + "***********" # name of the function arch_ffff => arch
		print  "\n" + tokens [0] # name of the block arch_ffff
		cnt+=1

#for fn in fn_list:
	#print str(fn)
	#for key, value in classes.iteritems():
	#		print str(key) +  "::" + str(value)
	#print "\n"

