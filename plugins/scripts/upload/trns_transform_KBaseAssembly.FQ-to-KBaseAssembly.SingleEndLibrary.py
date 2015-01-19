#!/usr/bin/env python
# This code is part of KBase project to validate 
#the fastq and fasta files

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

desc1 = '''
NAME
      trns_transform_KBaseAssembly.FQ-to-KBaseAssembly.SingleEndLibrary -- Converts the Fasta and Fastq files to KBaseAssembly.SingleEndLibrary (1.0)

SYNOPSIS      
      
'''

desc2 = '''
DESCRIPTION
  trns_transform_KBaseAssembly.FQ-to-KBaseAssembly.SingleEndLibrary converts the Fasta and Fastq files to KBaseAssembly.SingleEndLibrary 
  and returns a  json string of the particular type

  TODO: It will support KBase log format.
'''

desc3 = '''
AUTHORS
Srividya Ramakrishnan.

'''

### List of Exceptions
class Error(Exception):
    """Base class for exceptions in this module."""
    pass

def to_JSON(self):
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4)

	
def main(argv):
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter, prog='trns_transform_KBaseAssembly.FQ-to-KBaseAssembly.SingleEndLibrary', epilog=desc3)
    parser.add_argument('-s', '--shock_url', help='Shock url', action='store', dest='shock_url', default='https://kbase.us/services/shock-api')
    parser.add_argument('-n', '--hndl_svc_url', help='Handle service url', action='store', dest='hndl_url', default='https://kbase.us/services/handle_service')
    parser.add_argument('-i', '--in_id', help='Input Shock node id', action='store', dest='inobj_id', default=None, required=False)
    parser.add_argument('-f','--file_name', help = 'File Name', action= 'store', dest='file_name',default=None,required=False)
    parser.add_argument('-d','--hid', help = 'Handle id', action= 'store', dest='hid',default=None, required=False)
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
      try:
        args.hid = hs.persist_handle({ "id" : args.inobj_id , "type" : "shock" , "url" : args.shock_url})
      except:
        try:
          args.hid=hs.ids_to_handles([args.inobj_id])[0]["hid"]
        except:
          traceback.print_exc(file=sys.stderr)
          print >> sys.stderr, "Please provide handle id.\nThe input shock node id {} is already registered or could not be registered".format(args.inobj_id)
          exit(3)
    
    hds = hs.hids_to_handles([args.hid])

    if len(hds) <= 0: 
      print >> sys.stderr, 'Could not register a new handle with shock node id {} or wrong input handle id'.format(args.inobj_id)
      exit(2)

    ret = { "handle" : hds[0] }
    
    of = open(args.out_fn, "w")
    of.write(to_JSON(ret))
    of.close()

if __name__ == "__main__" :
    ret =  main(sys.argv[1:])
exit(0);

