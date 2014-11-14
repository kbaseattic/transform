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
import re
import json

desc1 = '''
NAME
      trns_validate_SBML -- validate uncompressed SBML file

SYNOPSIS      
      
'''

desc2 = '''
DESCRIPTION
  trns_validate_SBML validate uncompressed SBML file
'''

desc3 = '''
EXAMPLES
      > trns_validate_SBML -i test.sbml

AUTHORS
First Last.
'''

def validate (args) :

      in_dir = re.sub(r'/[^/]*$','', args.in_file)

      tcmd_lst = ['./validateSBML', in_dir]

      print tcmd_lst

      p1 = Popen(tcmd_lst, stdout=PIPE)
      out_str = p1.communicate()

      # print output message for error tracking
      if out_str[0] is not None : print out_str[0]
      if out_str[1] is not None : print >> sys.stderr, out_str[1]
     
     
      if p1.returncode != 0: 
          exit(p1.returncode) 

if __name__ == "__main__":
    # Parse options.
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter, prog='trns_validate_SBML', epilog=desc3)
    parser.add_argument('-i', '--in_file', help='Input file', action='store', dest='in_file', default=None, required=True)
    usage = parser.format_usage()
    parser.description = desc1 + '      ' + usage + desc2
    parser.usage = argparse.SUPPRESS
    args = parser.parse_args()

    validate(args)
    exit(0);
