# Test Script for Converting to Kbase format for Fasta files

### Test Paired End Conversion
### The json object created can be then saved in the workspace under KBaseAssembly.PairedEndLibrary
echo "PairedEndLibrary"
echo ""
/kb/dev_container/modules/transform/scripts/trns_transform_KBaseAssembly.FQ-to-KBaseAssembly.PairEndLibrary.py --in_id 74ac7ce3-7cfe-4332-9d27-4211cdc89792 74ac7ce3-7cfe-4332-9d27-4211cdc89792 --filepath ./test-fastq/Sample1.fastq ./test-fastq/Sample1.fastq  --hid dummy_handleid1 dummy_handleid2 -m 21.213 -k 2.232 -l True -r True --paired
echo ""
echo "This json object created can be then saved in the workspace under KBaseAssembly.PairedEndLibrary"
echo "######DONE######"
echo ""
echo "SingleEndLibrary"
echo ""
### Test Single End Conversion
### The json object created can be then saved in the workspace under KBaseAssembly.SingleEndLibrary
/kb/dev_container/modules/transform/scripts/trns_transform_KBaseAssembly.FQ-to-KBaseAssembly.SingleEndLibrary.py --in_id 74ac7ce3-7cfe-4332-9d27-4211cdc89792 --filepath ./test-fastq/Sample1.fastq --hid dummy_handleid1
echo ""
echo "This json object created can be then saved in the workspace under KBaseAssembly.SingleEndLibrary"
echo "######DONE######"
