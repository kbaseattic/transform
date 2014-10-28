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
      trnf_validator_Transform.CSV-1.0 -- validate CSV format for Transform module (version 1.0)

SYNOPSIS      
      
'''

desc2 = '''
DESCRIPTION
  trnf_validator_Transform.CSV-1.0 validate input CSV format for Transform module.
  If there is no error, it return 0. Otherwise, it return non-zero values and stderr message.

  TODO: It will support KBase log format.
'''

desc3 = '''
EXAMPLES
      CSV test case
      > trnf_validator_Transform.CSV-1.0 -i input_file.csv
      
SEE ALSO
      trnf_validator_handler

AUTHORS
First Last.
'''

def validator (args) :
    pass

if __name__ == "__main__":
    # Parse options.
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter, prog='trnf_validator_Transform.CSV-1.0', epilog=desc3)
    parser.add_argument('-i', '--in_file', help='Input file', action='store', dest='in_file', default=None, required=True)
    parser.add_argument('-a', '--optional_args', help='optional argument json string', action='store', dest='opt_args', default=None, required=False)
    usage = parser.format_usage()
    parser.description = desc1 + '      ' + usage + desc2
    parser.usage = argparse.SUPPRESS
    args = parser.parse_args()

    # main loop
    validator(args)
    exit(0);
