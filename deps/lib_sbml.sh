curl -O http://softlayer-dal.dl.sourceforge.net/project/sbml/libsbml/5.10.2/stable/libSBML-5.10.2-core-src.tar.gz
tar xvfz libSBML*
cd `ls -d libsbml-* | head -n 1`
./configure
make
make install
cd ..
rm -rf `ls -d libsbml-* | head -n 1`
rm -rf `ls libSBML* | head -n 1`
