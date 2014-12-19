# Test Script for Converting to Kbase format for Fasta files

### Test Paired End Conversion
### The json object created can be then saved in the workspace under KBaseAssembly.PairedEndLibrary
echo "PairedEndLibrary"
echo "################"
/kb/dev_container/modules/transform/scripts/trns_transform_KBaseAssembly.FA-to-KBaseAssembly.PairedEndLibrary.py -s http://10.1.16.87:7078 -n http://10.1.16.87:7109 -i 292157b0-0cae-40bd-8e10-3fe6c915c2c8 292157b0-0cae-40bd-8e10-3fe6c915c2c8 -f ./test-fasta/fasciculatum_supercontig.fasta ./test-fasta/fasciculatum_supercontig.fasta -o fasciculatum_supercontig_paired -m 23 -k 23123.2 -r 23
echo ""
echo " Interleaved PairedEnd"
echo " #####################"
/kb/dev_container/modules/transform/scripts/trns_transform_KBaseAssembly.FA-to-KBaseAssembly.PairedEndLibrary.py -s http://10.1.16.87:7078 -n http://10.1.16.87:7109 -i 292157b0-0cae-40bd-8e10-3fe6c915c2c8 -f ./test-fasta/fasciculatum_supercontig.fasta -o fasciculatum_supercontig_interleaved -m 23 -k 23123.2 -r 23 -l

echo "######DONE######"
