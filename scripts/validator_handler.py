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
import os
from optparse import OptionParser
from biokbase.workspace.client import Workspace
import urllib

desc1 = '''
NAME
      validator_handler -- validate the input data

SYNOPSIS      
      
'''

desc2 = '''
DESCRIPTION
  validator_handler call actual validation script to test wheather the input data is valid external data format or not
'''

desc3 = '''
EXAMPLES
      CSV test case
      > validator_handler --ws_url 'https://kbase.us/services/ws' --ws_id kbasetest:home  --in_id '' --out_id 'filtered_series' --method anova --p_value 0.01 
      
      Filter genes with LOR
      > validator_handler --ws_url 'https://kbase.us/services/ws' --ws_id KBasePublicExpression  --in_id 'my_series' -out_id 'filtered_series' --method lor --p_value 0.01 


SEE ALSO
      upload_handler, import_handler

AUTHORS
First Last.
'''

class AuthURLopener(urllib.FancyURLopener):
    Authorization= "OAuth {}".format(os.environ.get('KB_AUTH_TOKEN'))

urllib._urlopener = AuthURLopener()


def handler (args) :
    ###
    # download ws object and find where the validation script is located
    wsd = Workspace(url=args.ws_url, token=os.environ.get('KB_AUTH_TOKEN'))
    indata = wsd.get_object({'id' : args.etype,
                  'workspace' : args.sws_id})['data']

    if indata is None:
        raise Exception("Object {} not found in workspace {}".format(args.inobj_id, args.sws_id))

    try:
        os.mkdir(args.sdir)
    except:
        raise Exception("Could not create directory {}".format(args.sdir))

    if indata['validation_script']['id'] is None: raise Exception("Script Shock node id information is not provided")

    surl = args.shock_url
    if indata['validation_script']['shock_url'] is not None: surl = indata['validation_script']['shock_url']
    
    meta = urllib.urlopen("{}/node/{}".format(surl, indata['validation_script']['id']))
    script = urllib.urlopen("{}/node/{}?Download".format(surl, indata['id']))
    data = urllib.urlopen("{}/node/{}?Download".format(surl, args.inobj_id))
        
    # TODO: add compressed file handling using meta (tar.gz, tgz, etc).
    sif = open("{}/validator".format(args.sdir),'w')
    sif.write(script.read())
    sif.close()
    
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
    #if(args.del_tmps is "true") :
    #    os.remove("{}-{}".format(os.getpid(), args.exp_fn))
    #    os.remove("{}-{}".format(os.getpid(), args.flt_out_fn))

if __name__ == "__main__":
    # Parse options.
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter, prog='validator_handler', epilog=desc3)
    parser.add_argument('-u', '--ws_url', help='Workspace url', action='store', dest='ws_url', default='https://kbase.us/services/ws')
    parser.add_argument('-s', '--shock_url', help='Shock url', action='store', dest='shock_url', default='https://kbase.us/services/shock-api')
    parser.add_argument('-x', '--svc_ws_name', help='Service workspace name', action='store', dest='sws_id', default=None, required=True)
    parser.add_argument('-i', '--in_id', help='Input Shock node id', action='store', dest='inobj_id', default=None, required=True)
    parser.add_argument('-e', '--ext_type', help='External object type', action='store', dest='etype', default=None, required=True)
    parser.add_argument('-b', '--script_dir', help='Script directory', action='store', dest='sdir', default='bin')
    parser.add_argument('-d', '--del_script_dir', help='Delete script directory', action='store', dest='del_tmps', default='true')
    usage = parser.format_usage()
    parser.description = desc1 + '      ' + usage + desc2
    parser.usage = argparse.SUPPRESS
    args = parser.parse_args()

    # main loop
    handler(args)
    exit(0);
