# Test Script for Converting to Kbase format for Fasta files

echo "ReferenceAssembly"
echo ""

/kb/dev_container/modules/transform/scripts/trns_transform_KBaseAssembly.FA-to-KBaseAssembly.ReferenceAssembly.py -s http://10.1.16.87:7078 -n http://10.1.16.87:7109 -i 292157b0-0cae-40bd-8e10-3fe6c915c2c8 -f ./test-fasta/fasciculatum_supercontig.fasta -o fasciculatum_supercontig.fa -r fasciculatum_supercontig

echo "Please check the files fasciculatum_supercontig.fa ( workspace object type : KBaseAssembly.ReferenceAssembly )"
echo "DONE"
