## pvs-model-artifacts

`14 May 2019, @Amer Tahat @Pronnoy Gawsami @Sarang Joshi`

This directory includes all artifacts:

- To rerun the tests put the path of "rsl" directory to your PVS lib path.
- Test suites are large. To have a quick look at each one results you can look at the proof-summary of each test suit generated automatically in each directory. 

- `PVS7 version 7.0638` is necessary with a PVS patch (see PVS patches directory).The test suits and models have not been tested on other later development versions of PVS7. 
- The models are not compatible with any previous version. 


### Directories:
- `rsl`: has all the dependencies to run all the pvs files inside it. proof-summaries do exist for a quick look as well.
- `pvs_model_artifacts`: has all the formal-bit-format representations for all-ARMv8-A64 Instructions. Extracted directly from ASL-XML files. It includes all formal models for targets instructions and their classes.

`linux_zircon_pvs_models`: includes all formal models for Google Zircon extracted functions. It includes all formal models for Linux-vm-sample extracted functions.  
 

- To run the toolchain more dependencies must exist. See https://github.com/ssrg-vt/renee-artifacts/blob/master/README.md

