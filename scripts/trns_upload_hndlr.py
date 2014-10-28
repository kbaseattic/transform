#!/usr/bin/python
import argparse
import sys
import os
import time
import traceback
import sys
import ctypes
import subprocess
from subprocess import Popen, PIPE
import shutil
from optparse import OptionParser
from biokbase.workspace.client import Workspace
import urllib
import urllib2

desc1 = '''
NAME
      trnf_upload_handler -- upload the input data into WS

SYNOPSIS      
      
'''

desc2 = '''
DESCRIPTION
  trnf_upload_handler call actual trnf_validation_handler script to test 
  wheather the input data is valid external data format or not. If there is no
  error found, transform the input format to external format and save to WS.
  
'''

desc3 = '''
EXAMPLES
      CSV test case
      > trnf_upload_handler --ws_url 'https://kbase.us/services/ws' --ws_id kbasetest:home  --in_id '' --out_id 'my_tst_out'
      
      Filter genes with LOR
      > trnf_upload_handler --ws_url 'https://kbase.us/services/ws' --ws_id KBasePublicExpression  --in_id '' -out_id 'my_tst_out'


SEE ALSO
      trnf_validation_handler, trnf_import_handler

AUTHORS
First Last.
'''

def handler (args) :
    ###
    # download ws object and find where the validation script is located
    wsd = Workspace(url=args.ws_url, token=os.environ.get('KB_AUTH_TOKEN'))
    indata = wsd.get_object({'id' : args.etype,
                  'workspace' : args.sws_id})['data']

    if indata is None:
        raise Exception("Object {} not found in workspace {}".format(args.inobj_id, args.sws_id))

    try:
        shutil.rmtree(args.sdir)
    except:
        pass

    try:
        os.mkdir(args.sdir)
    except:
        raise Exception("Could not create directory {}".format(args.sdir))

    if 'id' not in indata['validation_script'] and indata['validation_script']['id'] is None: 
        raise Exception("Script Shock node id information is not provided")

    script_id = indata['validation_script']['id']
    surl = args.shock_url
    if 'shock_url' in indata['validation_script'] and indata['validation_script']['shock_url'] is not None: 
        surl = indata['validation_script']['shock_url']
    
    headers = {'Authorization' :  "OAuth {}".format(os.environ.get('KB_AUTH_TOKEN')) }
    content = {}
    body = urllib.urlencode(content)
    meta_req = urllib2.Request("{}/node/{}".format(surl, script_id))
    meta_req.add_header('Authorization',"OAuth {}".format(os.environ.get('KB_AUTH_TOKEN')))

    script_req = urllib2.Request("{}/node/{}?download_raw".format(surl, script_id));
    script_req.add_header('Authorization',"OAuth {}".format(os.environ.get('KB_AUTH_TOKEN')))

    data_req = urllib2.Request("{}/node/{}?download_raw".format(surl, args.inobj_id))
    data_req.add_header('Authorization',"OAuth {}".format(os.environ.get('KB_AUTH_TOKEN')))

    meta = urllib2.urlopen(meta_req)
    script = urllib2.urlopen(script_req)
    data = urllib2.urlopen(data_req)
        
    # TODO: add compressed file handling using meta (tar.gz, tgz, etc) using the configuration to choose what to execute and parameter handling.
    sif = open("{}/validator".format(args.sdir),'w')
    sif.write(script.read())
    sif.close()
    os.chmod("{}/validator".format(args.sdir),0700)
    
    dif = open("{}/in_file".format(args.sdir),'w')
    dif.write(data.read())
    dif.close()

    script.close()
    data.close()
    
    ###
    # execute validation
    vcmd_lst = ["{}/validator".format(args.sdir), "-i", "{}/in_file".format(args.sdir) ]

    p1 = Popen(vcmd_lst, stdout=PIPE)
    out_str = p1.communicate()
    # print output message for error tracking
    if out_str[0] is not None : print out_str[0]
    if out_str[1] is not None : print >> sys.stderr, out_str[1]

    # 
    if(args.del_tmps is "true") :
        try :
          shutil.rmtree("{}".format(args.sdir))
        except:
          pass

    if p1.returncode != 0: exit(p1.returncode) 

if __name__ == "__main__":
    # Parse options.
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter, prog='trnf_upload_handler', epilog=desc3)
    parser.add_argument('-u', '--ws_url', help='Workspace url', action='store', dest='ws_url', default='https://kbase.us/services/ws')
    parser.add_argument('-s', '--shock_url', help='Shock url', action='store', dest='shock_url', default='https://kbase.us/services/shock-api')
    parser.add_argument('-x', '--svc_ws_name', help='Service workspace name', action='store', dest='sws_id', default=None, required=True)
    parser.add_argument('-w', '--dst_ws_name', help='Destination workspace name', action='store', dest='ws_id', default=None, required=True)
    parser.add_argument('-i', '--in_id', help='Input Shock node id', action='store', dest='inobj_id', default=None, required=True)
    parser.add_argument('-o', '--out_id', help='Output workspace object name', action='store', dest='outobj_id', default=None, required=True)
    parser.add_argument('-e', '--ext_type', help='External object type', action='store', dest='etype', default=None, required=True)
    parser.add_argument('-b', '--script_dir', help='Script directory', action='store', dest='sdir', default='bin')
    parser.add_argument('-d', '--del_script_dir', help='Delete script directory', action='store', dest='del_tmps', default='true')
    usage = parser.format_usage()
    parser.description = desc1 + '      ' + usage + desc2
    parser.usage = argparse.SUPPRESS
    args = parser.parse_args()

    # main loop
    validation_handler(args)
    transform_handler(args)
    exit(0);
