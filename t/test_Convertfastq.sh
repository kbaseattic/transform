# Test Script for Converting to Kbase format for Fasta files

### Test Paired End Conversion
### The json object created can be then saved in the workspace under KBaseAssembly.PairedEndLibrary
echo "PairedEndLibrary"
echo ""
/kb/dev_container/modules/transform/scripts/trns_transform_KBaseAssembly.FQ-to-KBaseAssembly.PairedEndLibrary.py -i 5694465c-c7dd-48ea-a383-051e3d64e1f2,f64b2edd-59ef-4f77-949b-960a95b3867a -s http://10.1.16.87:7078 -n http://10.1.16.87:7109 -o  paired.json

### Test Single End Conversion
### The json object created can be then saved in the workspace under KBaseAssembly.SingleEndLibrary
/kb/dev_container/modules/transform/scripts/trns_transform_KBaseAssembly.FQ-to-KBaseAssembly.SingleEndLibrary.py -o SingleEnd.json -s http://10.1.16.87:7078 -n http://10.1.16.87:7109 -i 04935eff-a06c-403f-b40b-4922acf6303a -f ../t/test-fastq/Sample1.fastq
echo "Please check the files paired.json (workspace object type : KBaseAssembly.PairedEndLibrary), SingleEnd.json (workspace object type : KBaseAssembly.SingleEndLibrary)  "
echo "######DONE######"
