import re
ASL2PVS_fncnames_map = {}
ASL2PVS_types_map = {}
f = open ("sample.txt", "r")
# Read each line from the input file or dictionary whihc stores the extracted ASL declarations
for line in f:
	PVS_TYPE = ""
	PVS_fnc = ""
	conversion_fnc = ""
	extracted_field = ""
	line = line.strip()[:-1] 	# remove ;
	# Extract the field/s within the "()" in the ASL. For example "(Rd)" or "(op == '1')" => op == '1'		
	if "(" and ")" in line:
		paren_start = line.find("(")
		paren_end = line.find (")")
		extracted_field = line [paren_start+1: paren_end]				
	tokens = re.split("\s+", line)
	ASL_TYPE = tokens [0]
	type_name = tokens [1]
	operator = tokens [2]
	
	# Find the token which has "()"
	for token in tokens:
		parenthesis_idx = token.find("(")
		# Extract the name before "(" such as "Uint" in "Uint(Rd)"
		if parenthesis_idx > 0:  # Uint( or <no fnc>( op == "1")
			conversion_fnc = token[:parenthesis_idx]

	# Check the ASL_fnc_names dictionary if a fnc is present and return the PVS fnc if present else add it as a new type
	if conversion_fnc  in ASL2PVS_fncnames_map:
		PVS_fnc = ASL2PVS_fncnames_map[conversion_fnc]
	else:
		if conversion_fnc == "UInt":
			PVS_fnc = "bv2nat"
			ASL2PVS_fncnames_map [conversion_fnc] = PVS_fnc
	# Check the ASL_types dictionary if a type is present and return the PVS type if present else add it as a new type
	if ASL_TYPE in ASL2PVS_types_map:
		PVS_TYPE = ASL2PVS_types_map[ASL_TYPE]
	else:
		if ASL_TYPE == "integer":
			PVS_TYPE = "int"
			ASL2PVS_types_map[ASL_TYPE] = PVS_TYPE
		if ASL_TYPE == "boolean":
			PVS_TYPE = "bool"
			ASL2PVS_types_map[ASL_TYPE] = PVS_TYPE
	# Adding the translation to the output pvs file	
	if PVS_TYPE == "int":
		if type_name == "datasize":
			print "\t" + type_name + " : " + PVS_TYPE + " " + " " + operator + " 64"
		else:
			print "\t" + type_name + " : " + PVS_TYPE + " " + operator + " " + PVS_fnc + " (" + extracted_field +")"
	if PVS_TYPE == "bool":
		field_tokens = re.split("\s+", extracted_field)
		field_tokens [0] = "v'" + field_tokens[0] 	# TODO Check if the name of the variable in token[1] belongs to the diagram, in that case add v otherwise just use the token [0] name
		field_tokens [1] = field_tokens [1].replace("==", " = ")
		field_tokens [2] =  "bv ( 0b"  + field_tokens [2].replace ("'", "") + " )"
		new_fields = field_tokens [0] + field_tokens [1] + field_tokens [2]
		print  "\t" + type_name + " : " + PVS_TYPE + " "  + operator  + " (" + " " + new_fields + " )"





