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

def _get_node_download(shock_url,node, index=None, part=None, chunk=None, stream=False):
        if node == '':
            raise Exception(u'download requires non-empty node parameter')
        url = '%s/node/%s?download'%(shock_url, node)
        if index and part:
            url += '&index='+index+'&part='+str(part)
            if chunk:
                url += '&chunk_size='+str(chunk)
        try:
            rget = requests.get(url, headers=self.auth_header, stream=stream)
        except Exception as ex:
            message = self.template.format(type(ex).__name__, ex.args)
            raise Exception(u'Unable to connect to Shock server %s\n%s' %(url, message))
        if not (rget.ok):
            raise Exception(u'Unable to connect to Shock server %s: %s' %(url, rget.raise_for_status()))
        return rget

def download_to_path(shockurl,node, path, index=None, part=None, chunk=None):
	if path == '':
            raise Exception(u'download_to_path requires non-empty path parameter')
        result = _get_node_download(shockurl,node, index=index, part=part, chunk=chunk, stream=True)
        with open(path, 'wb') as f:
            for chunk in result.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    f.flush()
        return path
	
def main(argv):
   ret = 0
   parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter, prog='trnf_Convert_fastq', epilog=desc3)
   parser.add_argument('-s', '--shock_url', help='Shock url', action='store', dest='shock_url', default='https://kbase.us/services/shock-api')
   parser.add_argument('-i', '--in_id', help='Input Shock node id', action='store', dest='inobj_id', default=None, required=True,nargs='*')
   parser.add_argument('-f','--filepath', help = 'Path to the files', action= 'store', dest='loc_filepath',default=None,nargs='*',required=True)
   parser.add_argument('-d','--hid', help = 'Handle id', action= 'store', dest='hid',default=None,nargs='*',required=True)
   parser.add_argument('-m','--ins_mean', help = 'Mean insert size ( Only for Paired End Libraries)', action= 'store', dest='ins_mean',type=float,default=None)
   parser.add_argument('-k','--std_dev', help = 'Standard deviation ( Only for Paired End Libraries)', action= 'store', dest='std_dev',type=float,default=None)
   parser.add_argument('-l','--inl', help = 'Interleaved ( Only for Paired End Libraries)', action= 'store', dest='inl',default=None,type=bool)
   parser.add_argument('-r','--r_ori', help = 'Read Orientation ( Only for Paired End Libraries)', action= 'store', dest='read_orient',default=None,type=bool)
   parser.add_argument('-paired', '--paired_end', help='Turns paired-end option on', action='store_true',dest='paired',default=False)
   usage = parser.format_usage()
   parser.description = desc1 + ' ' + usage + desc2
   parser.usage = argparse.SUPPRESS
   args = parser.parse_args()
   kb_token = os.environ.get('KB_AUTH_TOKEN')	
   est = datetime.datetime.utcnow() + datetime.timedelta(minutes=3) 
   #print(args.loc_filepath)
   #print(args)
   #print(args.inobj_id)
   handle = []
   count = 0
   for i in args.loc_filepath:
		fname = os.path.basename(i)
		#fext = os.path.splitext(fname)		
		md5 = return_hash(i,hashlib.md5)
		sha1 = return_hash(i,hashlib.sha1)
		furl = args.shock_url+"/node/"+args.inobj_id[count]
		fid = args.inobj_id[count]		
		hdict = { "hid" : args.hid[count] , "file_name" : fname , "id" : fid , "type" : "fastq" , "url" : furl , "remote_md5" : md5 ,"remote_sha1" : sha1 } 
		handle.append(hdict)
		count += 1 

   if args.paired == False:
	ret  =  {"handle" : handle[0] }
   elif args.paired == True:
	ret = {"handle_1" : handle[0], "handle_2" :  handle[1]}
	if args.ins_mean is not None :
		ret["insert_size_mean"] = args.ins_mean
	if args.std_dev is not None:
		ret["insert_size_std_dev"] = args.std_dev
	if args.inl == True:
		ret["interleaved"] = 0
	if args.read_orient == True:
		 ret["read_orientation_outward"] = 0	
   #print(handle)
   return ret

if __name__ == "__main__" :
        ret =  main(sys.argv[1:])
        print(to_JSON(ret))
exit(0);

