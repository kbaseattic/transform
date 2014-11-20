#!/usr/bin/python
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

desc1 = '''
NAME
      trns_Convert_fastq -- Converts the Fasta and Fastq files to KBaseAssembly.SingleEndLibrary KBaseAssembly.PairedEndLibrary (1.0)

SYNOPSIS      
      
'''

desc2 = '''
DESCRIPTION
  trans_convert_fastq converts the Fasta and Fastq files to KBaseAssembly.SingleEndLibrary KBaseAssembly.PairedEndLibrary
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
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter, prog='trnf_Convert_fastq', epilog=desc3)
    parser.add_argument('-s', '--shock_url', help='Shock url', action='store', dest='shock_url', default='https://kbase.us/services/shock-api')
    parser.add_argument('-n', '--hndl_svc_url', help='Handle service url', action='store', dest='hndl_url', default='https://kbase.us/services/handle_service')
    parser.add_argument('-i', '--in_ids', help='Two input Shock node ids (comma separated)', action='store', dest='inobj_id', default=None, required=False,nargs=1)
    parser.add_argument('-f','--file_names', help = 'Two optional handle file names (comma separated)', action= 'store', dest='loc_filepath',default=None,nargs=1,required=False)
    parser.add_argument('-d','--hids', help = 'Two handle ids (comma separated)', action= 'store', dest='hid',default=None,required=False)
    parser.add_argument('-m','--ins_mean', help = 'Mean insert size', action= 'store', dest='ins_mean',type=float,default=None)
    parser.add_argument('-k','--std_dev', help = 'Standard deviation', action= 'store', dest='std_dev',type=float,default=None)
    parser.add_argument('-l','--inl', help = 'Interleaved  -- true/false', action= 'store', dest='inl',default=None)
    parser.add_argument('-r','--r_ori', help = 'Read Orientation -- true/false', action= 'store', dest='read_orient',default=None)
    parser.add_argument('-o', '--out_file_name', help='Output file name', action='store', dest='out_fn', default=None, required=True)
    usage = parser.format_usage()
    parser.description = desc1 + ' ' + usage + desc2
    parser.usage = argparse.SUPPRESS
    args = parser.parse_args()

    if args.inobj_id is None and args.hid is None:
      print >> sys.stderr, parser.description
      print >> sys.stderr, "Need to provide either shock node ids or handle ids"
      exit(1)

    kb_token = os.environ.get('KB_AUTH_TOKEN')	
    hs = AbstractHandle(url=args.hndl_url, token = kb_token)

    hids = []
    if args.hid is None:
      snids = args.inobj_id.split(',')
      if len(snids) != 2:
        print >> sys.stderr, "Please provide two shock node ids for pairend library"
        exit(4)
      try:
        hids.append(hs.persist_handle({ "id" : snids[0] , "type" : "shock" , "url" : args.shock_url}))
        hids.append(hs.persist_handle({ "id" : snids[1] , "type" : "shock" , "url" : args.shock_url}))
      except:
        print >> sys.stderr, "Please provide handle id.\nThe input shock node id {} is already registered or could not be registered".format(args.inobj_id)
        exit(3)
    else:
      hids = args.hid.split(',')
      if len(hids) != 2:
        print >> sys.stderr, "Please provide two handle ids for pairend library"
        exit(5)
    
    hds = hs.hids_to_handles(hids)
    if len(hds) != 2: 
      print >> sys.stderr, 'Could not register a new handle with shock node id {} or wrong input handle id'.format(args.inobj_id)
      exit(2)
    ret = {"handle_1" : hds[0], "handle_2" :  hds[1]}
    if args.ins_mean is not None :
    	ret["insert_size_mean"] = args.ins_mean
    if args.std_dev is not None:
    	ret["insert_size_std_dev"] = args.std_dev
    if args.inl == 'true':
    	ret["interleaved"] = 0
    if args.read_orient == 'true':
    	 ret["read_orientation_outward"] = 0	

    of = open(args.out_fn, "w")
    of.write(to_JSON(ret))
    of.close()

if __name__ == "__main__" :
    main(sys.argv[1:])
exit(0);

