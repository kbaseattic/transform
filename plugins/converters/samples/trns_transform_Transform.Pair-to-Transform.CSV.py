#!/usr/bin/env python

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
      trns_transform_Transform.Pair-to-Transform.CSV -- convert Transform.Pair format to CSV for download (version 1.0)

SYNOPSIS      
      
'''

desc2 = '''
DESCRIPTION
  trns_transform_Transform.Pair-to-Transform.CSV download Transform.Pair object and convert to CSV format.

  TODO: It will support KBase log format.
'''

desc3 = '''
EXAMPLES
      CSV conversion case
      > trns_transform_Transform.Pair-to-Transform.CSV -w ws_id -i obj_id 
      
SEE ALSO
      trns_download_hndlr

AUTHORS
First Last.
'''

def transform (args) :
    f = open(args.out_file, 'w')
    f.write('test_key,test_value')
    f.close()

if __name__ == "__main__":
    # Parse options.
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter, prog='trns_transform_Transform.Pair-to-Transform.CSV', epilog=desc3)
    parser.add_argument('-u', '--ws_url', help='Workspace url', action='store', dest='ws_url', default='https://kbase.us/services/ws')
    parser.add_argument('-w', '--ws_name', help='Workspace name', action='store', dest='ws_id', default=None, required=False)
    parser.add_argument('-i', '--in_name', help='Input workspace object name', action='store', dest='inobj_id', default=None, required=False)
    parser.add_argument('-o', '--out_file', help='Output file', action='store', dest='out_file', default=None, required=True)
    usage = parser.format_usage()
    parser.description = desc1 + '      ' + usage + desc2
    parser.usage = argparse.SUPPRESS
    args = parser.parse_args()

    # main loop
    transform(args)
    exit(0);
