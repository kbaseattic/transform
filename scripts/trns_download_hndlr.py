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
from biokbase.userandjobstate.client import UserAndJobState
from biokbase.Transform.util import Downloader
import mmap
import datetime

desc1 = '''
NAME
      trns_download_hndlr -- upload the input data into WS

SYNOPSIS      
      
'''

desc2 = '''
DESCRIPTION
  trns_download_hndlr call actual trnf_validation_handler script to test 
  wheather the input data is valid external data format or not. If there is no
  error found, transform the input format to external format and save to WS.
  
'''

desc3 = '''
EXAMPLES
      CSV test case
      > trns_download_hndlr --ws_url 'https://kbase.us/services/ws' --ws_id kbasetest:home  --in_id '' --out_id 'my_tst_out'
      
      Filter genes with LOR
      > trns_download_hndlr --ws_url 'https://kbase.us/services/ws' --ws_id KBasePublicExpression  --in_id '' -out_id 'my_tst_out'


SEE ALSO
      trns_validate_hndlr, trns_import_hndlr

AUTHORS
First Last.
'''

        
if __name__ == "__main__":
    # Parse options.
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter, prog='trns_download_hndlr', epilog=desc3)
    parser.add_argument('-u', '--ws_url', help='Workspace url', action='store', dest='ws_url', default='https://kbase.us/services/ws')
    parser.add_argument('-x', '--svc_ws_name', help='Service workspace name', action='store', dest='sws_id', default=None, required=True)
    parser.add_argument('-c', '--config_name', help='Script configuration workspace object name', action='store', dest='cfg_name', default=None, required=True)

    parser.add_argument('-w', '--src_ws_name', help='Source workspace name', action='store', dest='ws_id', default=None, required=True)
    parser.add_argument('-i', '--in_id', help='Input workspace object name', action='store', dest='inobj_id', default=None, required=True)

    parser.add_argument('-s', '--shock_url', help='Shock url', action='store', dest='shock_url', default='https://kbase.us/services/shock-api')

    parser.add_argument('-r', '--ujs_url', help='UJS url', action='store', dest='ujs_url', default='https://kbase.us/services/userandjobstate')
    parser.add_argument('-j', '--job_id', help='UJS job id', action='store', dest='jid', default=None, required=False)

    parser.add_argument('-e', '--ext_type', help='External object type', action='store', dest='etype', default=None, required=True)
    parser.add_argument('-t', '--kbase_type', help='KBase object type', action='store', dest='kbtype', default=None, required=True)

    parser.add_argument('-a', '--opt_args', help='Optional argument json string', action='store', dest='opt_args', default='{"downloader":{}}')

    parser.add_argument('-l', '--support_dir', help='Support directory', action='store', dest='sdir', default='lib')
    parser.add_argument('-d', '--del_lib_dir', help='Delete library directory', action='store', dest='del_tmps', default='true')
    parser.add_argument('-f', '--in_tmp_file', help='Input temporary file name', action='store', dest='itmp', default='infile')
    parser.add_argument('-g', '--out_tmp_file', help='Output temporary file name', action='store', dest='otmp', default='outfile')

    usage = parser.format_usage()
    parser.description = desc1 + '      ' + usage + desc2
    parser.usage = argparse.SUPPRESS
    args = parser.parse_args()

    kb_token = os.environ.get('KB_AUTH_TOKEN')
    ujs = UserAndJobState(url=args.ujs_url, token=kb_token)

    est = datetime.datetime.utcnow() + datetime.timedelta(minutes=3)
    if args.jid is not None:
      ujs.update_job_progress(args.jid, kb_token, 'Dispatched', 1, est.strftime('%Y-%m-%dT%H:%M:%S+0000') )


    ## main loop
    args.opt_args = json.loads(args.opt_args)
    #if 'downloader' not in args.opt_args:
    #  args.opt_args['uploader'] = {}
    #  args.opt_args['uploader']['file'] = args.otmp
    #  args.opt_args['uploader']['input'] = args.inobj_id
    #  args.opt_args['uploader']['jid'] = args.jid
    #  args.opt_args['uploader']['etype'] = args.etype
    downloader = Downloader(args)

    #try:
    #  downloader.download_ws_data()
    #except:
    #  if args.jid is not None:
    #    e,v,t = sys.exc_info()[:3]
    #    ujs.complete_job(args.jid, kb_token, 'Failed : data download from Workspace\n', str(v), {}) 
    #  else:
    #    traceback.print_exc(file=sys.stderr)
    #  exit(3);

    #if args.jid is not None:
    #  ujs.update_job_progress(args.jid, kb_token, 'Data downloaded', 1, est.strftime('%Y-%m-%dT%H:%M:%S+0000') )

    try:
      downloader.download_handler()
    except:
      if args.jid is not None:
        e,v = sys.exc_info()[:2]
        ujs.complete_job(args.jid, kb_token, 'Failed : data conversion\n', str(v), {}) 
      else:
        traceback.print_exc(file=sys.stderr)
      exit(4);

    if args.jid is not None:
      ujs.update_job_progress(args.jid, kb_token, 'Data converted', 1, est.strftime('%Y-%m-%dT%H:%M:%S+0000') )

    result = {}
    try:
      result = downloader.upload_to_shock()
    except:
      e,v = sys.exc_info()[:2]
      if args.jid is not None:
        ujs.complete_job(args.jid, kb_token, 'Failed : data upload to shock\n', str(v), {})
      else:
        traceback.print_exc(file=sys.stderr)
        print >> sys.stderr, 'Failed : data upload to shock\n{}:{}'.format(str(e),str(v))
      exit(5);
    print result

    # clean-up
    if(args.del_tmps is "true") :
        try :
          shutil.rmtree("{}".format(args.sdir))
        except:
          pass

    # TODO: Fix outobj_id to shock node id or we don't need shock node id...
    if args.jid is not None:
      ujs.complete_job(args.jid, kb_token, 'Succeed', None, {"shocknodes" : [result['id']], "shockurl" : args.shock_url, "workspaceids" : [], "workspaceurl" : args.ws_url ,"results" : [{"server_type" : "shock", "url" : args.shock_url, "id" : result['id'], "description" : "description"}]})
    else:
      print "{}/node/{}?download_raw".format(args.shock_url, result['id'])
    exit(0);
