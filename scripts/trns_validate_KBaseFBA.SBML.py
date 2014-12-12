#!/usr/bin/python
# This code is part of KBase project to validate 
#the sbml files

from __future__ import print_function

import math
import sys, getopt
import os.path
import subprocess
import json
import gzip
import io
import cStringIO

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

### List of Exceptions
class Error(Exception):
    """Base class for exceptions in this module."""
    pass

#class CalledProcessError(Exception):
#       pass

io_method = cStringIO.StringIO

def check_output(*popenargs, **kwargs):
    r"""Run command with arguments and return its output as a byte string.
    """
    error = ''
    status = ''
    if 'stdout' in kwargs:
        raise ValueError('stdout argument not allowed, it will be overridden.')
    process = subprocess.Popen(*popenargs,stdout=subprocess.PIPE)
    output, unused_err = process.communicate()
    retcode = process.poll()
    if retcode:
        cmd = kwargs.get("args")
        if cmd is None:
                 cmd = popenargs[0]
                 status = 'FAILED'
                 error = output
    else:
        status = 'SUCCESS'
    return {'status' : status, 'error' : error}

def to_JSON(self):
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4)

def validate_fasta(filename):
        ret = ''
        if os.path.isfile(filename):
                cmd2 = [impt,filename]
		print(cmd2)
                ret = check_output(cmd2,stderr=sys.stderr)
	else:
		print("File " + filename + " does not exist ")
		sys.exit(1)
        return ret

class Validate(object):
        """ Validate the object and return 0 or exit with an error
        """
        def __init__(self,filename):
                """ Initialize the validation function to proceed with validation
                """
		if os.path.isfile(filename):
                	self.filename = filename
                        func = validate_fasta
                else:
		     print("File " + filename + " doesnot exist ")
		     sys.exit(1)
	
                ret = func(filename)
                if "status" in ret.keys():
                        self.status = ret["status"]
                if "error" in ret.keys():
                        self.error = ret["error"]

def usage():
        print("Usage : trns_validate_KBaseFBA.SBML.py -i <filename> ")

def main(argv):
   inputfile = ''
   ret = None
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
         inputfile = arg
         ret = Validate(inputfile)
      else:
        print('Invalid Option' + usage())

   return ret

if __name__ == "__main__" :
   if len(sys.argv) != 1:
        ret =  main(sys.argv[1:])
        print(to_JSON(ret))
   else:
        usage()
exit(0);

