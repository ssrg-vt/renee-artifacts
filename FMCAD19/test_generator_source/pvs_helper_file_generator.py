# A script to use the pickled files that contain the ASL2PVS basic fnc and basic type signatures and print them out to the utils dir

import pickle
import os
pvs_fn_signatures = []
pvs_types = []


output_dir = "utils_data/"
# Load the pickled fn and types into the lists
def unpickle_lists():
	filename_fn = output_dir + "pickled_pvs_fn"
	infile_fn = open(filename_fn,'rb')
	pvs_fn_signatures = pickle.load(infile_fn)
	infile_fn.close()

	filename_types = output_dir + "pickled_pvs_types"
	infile_types = open(filename_types,'rb')
	pvs_types = pickle.load(infile_types)
	infile_types.close()

	output_filename1 = output_dir + "ASL_fnc.pvs"
	if os.path.exists(output_filename1):
    		append_write = 'a' # append if already exists
	else:
    		append_write = 'w'	
	output_fn_file = open (output_filename1 ,append_write)
	for signature in pvs_fn_signatures:
		output_fn_file.write (signature + "\n")

	output_filename2 = output_dir + "ASL_types.pvs"
	if os.path.exists(output_filename2):
		append_write = 'a' # append if already exists
	else:
		append_write = 'w'	
	output_types_file = open ( output_filename2 ,append_write)
	for pvs_type in pvs_types:
		output_types_file.write (pvs_type)


unpickle_lists()

