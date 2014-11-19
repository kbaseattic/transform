#!/usr/bin/python
# This code is part of KBase project to validate 
#the fastq and fasta files

from __future__ import print_function

import math
import sys, getopt
import argparse
import os.path
import subprocess
import json
import gzip
import io
import cStringIO
import hashlib
#from biokbase.workspace.client import Workspace
import urllib
import urllib2
import datetime
#from biokbase import log
#from biokbase.Transform.util import download_shock_data, validation_handler, transformation_handler,upload_to_ws

desc1 = '''
NAME
      trns_Convert_fastq -- Convert the Fastq files to a kbase types SingleEndLibrary , PairedEndLibrary (1.0)

SYNOPSIS      
      
'''

desc2 = '''
DESCRIPTION
  trans_convert_fastq validate the fasta and fastq file and returns
  a json string

  TODO: It will support KBase log format.
'''

desc3 = '''
EXAMPLES
   > trns_trans_convert_fastq -i <Input fasta or fastq file>

AUTHORS
Srividya Ramakrishnan.
'''

handle_service_url  = "http://140.221.67.78:7109"
io_method = cStringIO.StringIO
BLOCKSIZE = 65536

### List of Exceptions
class Error(Exception):
    """Base class for exceptions in this module."""
    pass

def return_hash(filename,func):
	hasher = func()
	with open(filename, 'rb') as afile:
    		buf = afile.read(BLOCKSIZE)
    		while len(buf) > 0:
			hasher.update(buf)
			buf = afile.read(BLOCKSIZE)
	return hasher.hexdigest()
	
def to_JSON(self):
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4)

	
def main(argv):
   ret = 0
   parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter, prog='trnf_Convert_fastq', epilog=desc3)
   parser.add_argument('-s', '--shock_url', help='Shock url', action='store', dest='shock_url', default='https://kbase.us/services/shock-api')
   parser.add_argument('-i', '--in_id', help='Input Shock node id', action='store', dest='inobj_id', default=None, required=True)
   parser.add_argument('-f','--filepath', help = 'Path to the files', action= 'store', dest='loc_filepath',default=None,required=True)
   parser.add_argument('-d','--hid', help = 'handle id', action= 'store', dest='hid',default=None,required=True)
   usage = parser.format_usage()
   parser.description = desc1 + ' ' + usage + desc2
   parser.usage = argparse.SUPPRESS
   args = parser.parse_args()
   #print(args.loc_filepath)
   #print(args)
   #print(args.inobj_id)
   fname = os.path.basename(args.loc_filepath)
   ref_name,fext = os.path.splitext(fname)		
   md5 = return_hash(args.loc_filepath,hashlib.md5) 
   sha1 = return_hash(args.loc_filepath,hashlib.sha1)
   furl = args.shock_url+"/node/"+args.inobj_id
   fid = args.inobj_id		
   hdict = { "hid" : args.hid , "file_name" : fname , "id" : fid , "type" : "fasta" , "url" : furl , "remote_md5" : md5 ,"remote_sha1" : sha1 } 
   ret = { "handle" : hdict , "reference_name" : ref_name}
   return ret

if __name__ == "__main__" :
        ret =  main(sys.argv[1:])
        print(to_JSON(ret))
exit(0);

