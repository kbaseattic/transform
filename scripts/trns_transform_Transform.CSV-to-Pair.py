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
      trns_transform_Transform.CSV-to-Pair -- convert CSV format to Pair for Transform module (version 1.0)

SYNOPSIS      
      
'''

desc2 = '''
DESCRIPTION
  trns_transform_Transform.CSV-to-Pair convert input CSV format to Pair typed 
  json string file for Transform module.

  TODO: It will support KBase log format.
'''

desc3 = '''
EXAMPLES
      CSV conversion case
      > trns_transform_Transform.CSV-to-Pair -i input_file.csv -o ouput_file.json
      
SEE ALSO
      trns_upload_hndlr

AUTHORS
First Last.
'''

def transform (args) :
    try:
      ofh = open(args.out_file,'w')
      ofh.write('{"key" : "test_key", "value" : "test_value" }')
      ofh.close()
    except:
      raise Exception("Error writing to {}".format(args.out_file))

if __name__ == "__main__":
    # Parse options.
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter, prog='trns_transform_Transform.CSV-to-Pair', epilog=desc3)
    parser.add_argument('-i', '--in_file', help='Input file', action='store', dest='in_file', default=None, required=True)
    parser.add_argument('-o', '--out_file', help='Output file', action='store', dest='out_file', default=None, required=True)
    parser.add_argument('-a', '--optional_args', help='optional argument json string', action='store', dest='opt_args', default=None, required=False)
    usage = parser.format_usage()
    parser.description = desc1 + '      ' + usage + desc2
    parser.usage = argparse.SUPPRESS
    args = parser.parse_args()

    # main loop
    transform(args)
    exit(0);
