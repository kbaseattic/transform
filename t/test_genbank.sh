java -cp $CP us.kbase.genbank.ValidateGBK /kb/dev_container/modules/transform/t/genbank/NC_005213
java -cp $CP us.kbase.genbank.ValidateGBK /kb/dev_container/modules/transform/t/genbank/NC_009925

java -cp $CP us.kbase.genbank.ConvertGBK /kb/dev_container/modules/transform/t/genbank/NC_005213 loader_test http://localhost:7058 
java -cp $CP us.kbase.genbank.ConvertGBK /kb/dev_container/modules/transform/t/genbank/NC_009925 loader_test http://localhost:7058
