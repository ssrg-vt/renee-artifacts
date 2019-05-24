f = open("all_mains", "r")
f2 = open ("top_input", "w")
for line in f:
	line = line.strip().replace(".pvs", "")
	f2.write ("IMPORTING " + line + "\n")
f.close()
f2.close()
	
