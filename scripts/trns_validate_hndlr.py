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
from biokbase.Transform.util import download_shock_data, validation_handler, transformation_handler,upload_to_ws
from biokbase import log

desc1 = '''
NAME
      trns_validate_hndlr -- validate the input data

SYNOPSIS      
      
'''

desc2 = '''
DESCRIPTION
  trns_validate_hndlr call actual validation script to test wheather the input data is valid external data format or not
'''

desc3 = '''
EXAMPLES
      CSV test case
      > trns_validate_hndlr -i 'your_shock_node_id' -e Transform.CSV

SEE ALSO
      upload_handler, import_handler

AUTHORS
First Last.
'''

if __name__ == "__main__":
    # Parse options.
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter, prog='trns_validate_hndlr', epilog=desc3)
    parser.add_argument('-u', '--ws_url', help='Workspace url', action='store', dest='ws_url', default='https://kbase.us/services/ws')
    parser.add_argument('-x', '--svc_ws_name', help='Service workspace name', action='store', dest='sws_id', default=None, required=True)
    parser.add_argument('-c', '--config_name', help='Script configuration workspace object name', action='store', dest='cfg_name', default=None, required=True)

    parser.add_argument('-s', '--shock_url', help='Shock url', action='store', dest='shock_url', default='https://kbase.us/services/shock-api')
    parser.add_argument('-i', '--in_id', help='Input Shock node id', action='store', dest='inobj_id', default=None, required=True)

    parser.add_argument('-e', '--ext_type', help='External object type', action='store', dest='etype', default=None, required=True)

    parser.add_argument('-a', '--opt_args', help='Optional argument json string', action='store', dest='opt_args', default='{"validator":{},"transformer":{}}')
    parser.add_argument('-j', '--job_id', help='UJS job id', action='store', dest='jid', default=None, required=True)

    parser.add_argument('-l', '--support_dir', help='Support directory', action='store', dest='sdir', default='lib')
    parser.add_argument('-d', '--del_lib_dir', help='Delete library directory', action='store', dest='del_tmps', default='true')
    parser.add_argument('-f', '--in_tmp_file', help='Input temporary file name', action='store', dest='itmp', default='infile')

    usage = parser.format_usage()
    parser.description = desc1 + '      ' + usage + desc2
    parser.usage = argparse.SUPPRESS
    args = parser.parse_args()


    config = {}
    config


    # main loop
    args.opt_args = json.loads(args.opt_args)
    download_shock_data(args.shock_url, args.inobj_id, args.sdir, args.itmp)
    validation_handler(args.ws_url, args.cfg_name, args.sws_id, args.etype, args.sdir, args.itmp, args.opt_args, "", args.jid)

    # clean-up
    if(args.del_tmps is "true") :
        try :
          shutil.rmtree("{}".format(args.sdir))
        except:
          pass

    exit(0);
