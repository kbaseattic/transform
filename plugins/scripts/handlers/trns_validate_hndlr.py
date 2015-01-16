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
import json
from biokbase import log
from biokbase.userandjobstate.client import UserAndJobState
from biokbase.Transform.util import Validator
import datetime

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
    parser = argparse.ArgumentParser()
    parser.add_argument('--ujs_service_url', help='UJS url', action='store', default='https://kbase.us/services/userandjobstate')
    parser.add_argument('--ujs_job_id', help='UJS job id', action='store', default=None, required=False)
    parser.add_argument('--external_type', help='External object type', action='store', default=None, required=True)
    parser.add_argument('--optional_arguments', help='Optional argument json string', action='store')

    parser.add_argument('--working_directory', help='Support directory', action='store', default='lib')
    parser.add_argument('--delete_working_directory', help='Delete library directory', action='store_true')
    parser.add_argument('--in_tmp_file', help='Input temporary file name', action='store', default='infile')

    args = parser.parse_args()

    kb_token = os.environ.get('KB_AUTH_TOKEN')
    ujs = UserAndJobState(url=args.ujs_url, token=kb_token)

    est = datetime.datetime.utcnow() + datetime.timedelta(minutes=3)
    if args.jid is not None:
        ujs.update_job_progress(args.jid, kb_token, 'Dispatched', 1, est.strftime('%Y-%m-%dT%H:%M:%S+0000'))

    # main loop
    args.optional_arguments = json.loads(args.optional_arguments)

    validator = Validator(args)

    try:
        validator.validation_handler()
    except:
        e,v = sys.exc_info()[:2]
        if args.jid is not None:
            ujs.complete_job(args.jid, kb_token, 'Failed : data validation\n{}:{}'.format(str(e),str(v)), str(e), {}) 
        else:
            traceback.print_exc(file=sys.stderr)
            print sys.stderr, 'Failed : data validation\n{}:{}'.format(str(e),str(v))
            sys.exit(1);

    # clean-up
    if args.delete_working_directory:
        try :
            shutil.rmtree("{}".format(args.working_directory))
        except:
            pass

    if args.jid is not None:
        ujs.complete_job(args.ujs_job_id, kb_token, 'Success', None, None)
    sys.exit(0);
