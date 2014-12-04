# Test Script for Converting to Kbase format for Fasta files

/kb/dev_container/modules/transform/scripts/trns_transform_KBaseAssembly.FA-to-KBaseAssembly.ReferenceAssembly.py -s http://10.1.16.87:7078 -n http://10.1.16.87:7109 -i d777a897-8630-4016-8e3a-87c6bc36e2cd -w testfa -f ./test-fasta/Sample1.fa -o fasta.json

echo "Please check the files fasta.json ( workspace object type : KBaseAssembly.ReferenceAssembly )"
echo "DONE"
