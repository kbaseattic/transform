#!/usr/bin/env python
# This code is part of KBase project to validate 
#the fastq and fasta files

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
      trns_validate_KBaseAssembly.FA -- Validate the fasta files (1.0)

SYNOPSIS      
      
'''

desc2 = '''
DESCRIPTION
  trns_validate_KBaseAssembly.FA validate the fasta file and returns
  a json string

  TODO: It will support KBase log format.
'''

desc3 = '''
EXAMPLES
   > trns_trns_validate_KBaseAssembly.FA -i <Input fasta file>

AUTHORS
Srividya Ramakrishnan.
'''

impt = os.environ.get("KB_TOP")+"/lib/jars/FastaValidator/FastaValidator-1.0.jar"

mc = 'FVTester'

#### Extensions supported for fastq and fasta
fastq_ext = ['.fq','.fq.gz','.fastq','.fastq.gz']
fasta_ext = ['.fa','.fa.gz','.fasta','.fasta.gz']


####File executables
fval_path= "fastQValidator"
#if os.environ.get("KB_RUNTIME") is not None:
#	fast_path = os.environ.get("KB_RUNTIME")+'/lib'
#else:
#	print("Environmental variable KB_RUNTIME" + " is not set")
#	sys.exit(1)
#fast_path = "/kb/runtime/lib/"

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
        kb_runtime = os.environ.get('KB_RUNTIME', '/kb/runtime')
        java = "%s/java/bin/java" % kb_runtime
        if os.path.isfile(filename):
                ext = os.path.splitext(filename)[-1]
                if ext == '.gz':
                        decomp_file = os.path.splitext(filename)[-2]
                        p = subprocess.Popen(["zcat", filename], stdout = subprocess.PIPE)
                        fh = io_method(p.communicate()[0])
                        assert p.returncode == 0
                        text_file = open(decomp_file, "w")
                        text_file.write(fh.getvalue())
                        text_file.close()
                if ext == '.gz':
                        cmd2 = [java,"-classpath",impt,mc,os.path.splitext(filename)[-2]]
		else:
			cmd2 = [java,"-classpath",impt,mc,filename]
		#print(cmd2)
                ret = check_output(cmd2,stderr=sys.stderr)
	else:
		print("File " + filename + " doesnot exist ")
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
        print("Usage : trns_validate_KBaseAssembly.FA -i <filename> ")

def main(argv):
   inputfile = ''
   ret = None
   try:
      opts, args = getopt.getopt(argv,"hi:")
   except getopt.GetoptError:
      print('trns_validate_KBaseAssembly.FA -i <inputfile>')
      sys.exit(2)
   for opt, arg in opts:
      if opt == '-h':
         print('trns_validate_KBaseAssembly.FA -i <inputfile>')
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

