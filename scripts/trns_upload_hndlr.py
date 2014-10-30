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
import json
from biokbase import log
from biokbase.Transform.util import download_shock_data, validation_handler, transformation_handler,upload_to_ws

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
      trns_validate_hndlr, trns_import_hndlr

AUTHORS
First Last.
'''

if __name__ == "__main__":
    # Parse options.
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter, prog='trnf_upload_handler', epilog=desc3)
    parser.add_argument('-u', '--ws_url', help='Workspace url', action='store', dest='ws_url', default='https://kbase.us/services/ws')
    parser.add_argument('-x', '--svc_ws_name', help='Service workspace name', action='store', dest='sws_id', default=None, required=True)
    parser.add_argument('-c', '--config_name', help='Script configuration workspace object name', action='store', dest='cfg_name', default=None, required=True)

    parser.add_argument('-s', '--shock_url', help='Shock url', action='store', dest='shock_url', default='https://kbase.us/services/shock-api')
    parser.add_argument('-i', '--in_id', help='Input Shock node id', action='store', dest='inobj_id', default=None, required=True)

    parser.add_argument('-r', '--ujs_url', help='UJS url', action='store', dest='ujs_url', default='https://kbase.us/services/userandjobstate')
    parser.add_argument('-j', '--job_id', help='UJS job id', action='store', dest='jid', default=None, required=True)

    parser.add_argument('-w', '--dst_ws_name', help='Destination workspace name', action='store', dest='ws_id', default=None, required=True)
    parser.add_argument('-o', '--out_id', help='Output workspace object name', action='store', dest='outobj_id', default=None, required=True)

    parser.add_argument('-e', '--ext_type', help='External object type', action='store', dest='etype', default=None, required=True)
    parser.add_argument('-t', '--kbase_type', help='KBase object type', action='store', dest='kbtype', default=None, required=True)

    parser.add_argument('-a', '--opt_args', help='Optional argument json string', action='store', dest='opt_args', default='{"validator":{},"transformer":{}}')

    parser.add_argument('-l', '--support_dir', help='Support directory', action='store', dest='sdir', default='lib')
    parser.add_argument('-d', '--del_lib_dir', help='Delete library directory', action='store', dest='del_tmps', default='true')
    parser.add_argument('-f', '--in_tmp_file', help='Input temporary file name', action='store', dest='itmp', default='infile')
    parser.add_argument('-g', '--out_tmp_file', help='Output temporary file name', action='store', dest='otmp', default='outfile')

    usage = parser.format_usage()
    parser.description = desc1 + '      ' + usage + desc2
    parser.usage = argparse.SUPPRESS
    args = parser.parse_args()

    # main loop
    args.opt_args = json.loads(args.opt_args)
    download_shock_data(args.shock_url, args.inobj_id, args.sdir, args.itmp)
    validation_handler(args.ws_url, args.cfg_name, args.sws_id, args.etype, args.sdir, args.itmp, args.opt_args, "", args.jid)
    transformation_handler(args.ws_url, args.cfg_name, args.sws_id, args.etype, args.kbtype, args.sdir, args.itmp, args.otmp, args.opt_args, "", args.jid)
    upload_to_ws(args.ws_url,args.sdir, args.otmp, args.ws_id, args.kbtype, args.outobj_id, args.inobj_id, args.etype, args.jid)

    # clean-up
    if(args.del_tmps is "true") :
        try :
          shutil.rmtree("{}".format(args.sdir))
        except:
          pass

    exit(0);
