#!/usr/bin/python
# This code is part of KBase project to validate 
#the sbml files

import sys, getopt
import os.path
import subprocess
import json
import logging

# KBase imports
import biokbase.Transform.script_utils as script_utils

desc1 = '''
NAME
      trns_validate_KBaseFBA.SBML.py -- Validate the fasta files (1.0)

SYNOPSIS      
      
'''

desc2 = '''
DESCRIPTION
  trns_validate_KBaseFBA.SBML.py validate the fasta file and returns
  a json string

  TODO: It will support KBase log format.
'''

desc3 = '''
EXAMPLES
   > trns_validate_KBaseFBA.SBML.py -i <Input fasta file>

AUTHORS
Srividya Ramakrishnan; Sam Seaver
'''

impt = "../bin/validateSBML"

def to_JSON(self):
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4)

class Validate(object):
        """ Validate the object and return 0 or exit with an error
        """
        def __init__(self,filename):
                """ Initialize the validation function to proceed with validation
                """
                self.filename=filename
                cmd = [impt,filename]
                process = subprocess.Popen(cmd,stdout=subprocess.PIPE)
                output, unused_err = process.communicate()
                retcode = process.poll()

                error = ''
                status = ''

                if retcode:
                    self.status = 'FAILED'
                    self.error = output
                else:
                    self.status = 'SUCCESS'

def usage():
        print("Usage : trns_validate_KBaseFBA.SBML.py -i <filename> ")

def main(argv):
   inputfile = ''
   ret = None
   logger = script_utils.getStderrLogger(__file__)

   logger.info("Validation of SBML")

   try:
      opts, args = getopt.getopt(argv,"hi:")
   except getopt.GetoptError:
      print('trns_validate_KBaseFBA.SBML.py -i <inputfile>')
      sys.exit(2)

   for opt, arg in opts:
      if opt == '-h':
         print('trns_validate_KBaseFBA.SBML.py -i <inputfile>')
         sys.exit()
      elif opt == "-i":
         if os.path.isfile(arg):
             ret = Validate(arg)
         else:
             logger.warn("File " + arg + " does not exist ")
             print("File " + arg + " does not exist ")
             sys.exit(1)
      else:
        logger.warn("Invalid Option "+usage())
        print('Invalid Option ' + usage())

   return ret

if __name__ == "__main__" :
   if len(sys.argv) != 1:
        ret = main(sys.argv[1:])
        print(to_JSON(ret))
   else:
        usage()
exit(0);
