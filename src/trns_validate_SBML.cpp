/**
 * @file    validateSBML.cpp
 * @brief   Validates an SBML file against the appropriate schema; compiled as g++ -o ../bin/validateSBML ../src/trns_validate_SBML.cpp -lsbml
 * @author  Sam Seaver (heavily borrowed from libsbml example)
 */

#include <iostream>
#include <sstream>

#include <sbml/SBMLTypes.h>

using namespace std;
LIBSBML_CPP_NAMESPACE_USE

bool validateSBML(const string& filename);

const string usage = "Usage: validateSBML filename\n";

int
main (int argc, char* argv[])
{
  if (argc < 2){
    cout << usage << endl;
    return 1;
  }

  return validateSBML(argv[1]);
}


bool validateSBML(const string& filename){
  SBMLDocument* document;
  SBMLReader reader;

  document = reader.readSBML(filename);

  unsigned int errors = document->getNumErrors();
  bool  seriousErrors = false;
  bool        isValid = true;

  unsigned int numReadErrors   = 0;
  unsigned int numReadWarnings = 0;
  string       errMsgRead      = "";

  if (errors > 0){
    for (unsigned int i = 0; i < errors; i++){
      if (document->getError(i)->isFatal() || document->getError(i)->isError()){
        seriousErrors = true;
	++numReadErrors;
        break;
      }else{
        ++numReadWarnings;
      }
    }

    ostringstream oss;
    document->printErrors(oss);
    errMsgRead = oss.str();
  }

  if(seriousErrors){
    isValid = false;
  }

  if(numReadErrors > 0){
    cout << "validation error(s) : " << numReadErrors << endl;
    if ( !errMsgRead.empty() ){
      cout << "\n===== validation error/warning messages =====\n";
      cout << errMsgRead << endl;
    }
  }
  //  cout << "    validation warning(s) : " << numReadWarnings << endl;
  
  delete document;

  return (isValid) ? false: true;
}
