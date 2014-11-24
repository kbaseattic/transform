#!/usr/bin/python
# This code is part of KBase project to validate 
#the fastq and fasta files

#from __future__ import print_function

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
import urllib
import urllib2
import datetime
from biokbase.AbstractHandle.Client import AbstractHandle
import traceback
#from biokbase import log

desc1 = '''
NAME
      trns_transform_KBaseAssembly.FA-to-KBaseAssembly.ReferenceAssembly -- Convert the Fasta files to kbase types KBaseAssembly.ReferenceAssembly

SYNOPSIS      
      
'''

desc2 = '''
DESCRIPTION
  trns_transform_KBaseAssembly.FA-to-KBaseAssembly.ReferenceAssembly converts the external Fasta files to  kbase types KBaseAssembly.ReferenceAssembly

  TODO: It will support KBase log format.
'''

desc3 = '''
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
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter, prog='trns_transform_KBaseAssembly.FA-to-KBaseAssembly.ReferenceAssembly', epilog=desc3)
    parser.add_argument('-s', '--shock_url', help='Shock url', action='store', dest='shock_url', default='https://kbase.us/services/shock-api')
    parser.add_argument('-n', '--hndl_svc_url', help='Handle service url', action='store', dest='hndl_url', default='https://kbase.us/services/handle_service')
    parser.add_argument('-i', '--in_id', help='Input Shock node id', action='store', dest='inobj_id', default=None, required=False)
    parser.add_argument('-w','--reference_name', help = 'Reference Name', action= 'store', dest='ref_name',default=None,required=False)
    parser.add_argument('-f','--file_name', help = 'File Name', action= 'store', dest='file_name',default=None,required=False)
    parser.add_argument('-d','--hid', help = 'handle id', action= 'store', dest='hid',default=None,required=False)
    parser.add_argument('-o', '--out_file_name', help='Output file name', action='store', dest='out_fn', default=None, required=True)
    usage = parser.format_usage()
    parser.description = desc1 + ' ' + usage + desc2
    parser.usage = argparse.SUPPRESS
    args = parser.parse_args()
    
    if args.inobj_id is None and args.hid is None:
      print >> sys.stderr, parser.description
      print >> sys.stderr, "Need to provide either shock node id or handle id"
      exit(1)
    
    kb_token = os.environ.get('KB_AUTH_TOKEN')
    hs = AbstractHandle(url=args.hndl_url, token = kb_token)
    
    if args.hid is None:
      try: # to create one
        args.hid = hs.persist_handle({ "id" : args.inobj_id , "type" : "shock" , "url" : args.shock_url})
        hds = hs.hids_to_handles([args.hid])
      except: # handle is already registered
        try:
          hds = hs.ids_to_handles([args.inobj_id]) # look up by shock_node id
        except:
          traceback.print_exc(file=sys.stderr)
          print >> sys.stderr, "Please provide handle id.\nThe input shock node id {} is already registered or could not be registered".format(args.inobj_id)
          exit(3)
    else : # given handle_id
      hds = hs.hids_to_handles([args.hid]) 

    if len(hds) <= 0: 
      print >> sys.stderr, 'Could not register a new handle with shock node id {} or wrong input handle id'.format(args.inobj_id)
      exit(2)

    ret = { "handle" : hds[0] }
    if args.ref_name is not None:
      ret['reference_name'] = args.ref_name
    
    of = open(args.out_fn, "w")
    of.write(to_JSON(ret))
    of.close()

if __name__ == "__main__" :
    ret =  main(sys.argv[1:])

exit(0);
