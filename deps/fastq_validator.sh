git clone https://github.com/statgen/fastQValidator.git
git clone https://github.com/statgen/libStatGen.git
cd libStatGen; make; cd ..
cd fastQValidator; make; cd ..
cp ./fastQValidator/bin/fastQValidator $KB_RUNTIME/bin
rm -rf fastQValidator libStatGen
