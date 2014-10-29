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
import mmap

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

def download_handler (ws_url, cfg_name, sws_id, ws_id, in_id, etype, kbtype, sdir, otmp, opt_args, ujs_url, ujs_jid) :
    #TODO: Improve folder checking
    try:
        os.mkdir(sdir)
    except:
        pass

    ###
    # download ws object and find where the validation script is located
    wsd = Workspace(url=ws_url, token=os.environ.get('KB_AUTH_TOKEN'))
    # TODO: get subobject
    config = wsd.get_object({'id' : cfg_name, 'workspace' : sws_id})['data']['config_map']

    if config is None:
        raise Exception("Object {} not found in workspace {}".format(etype, sws_id))
    
    ###
    # execute validation
    
    ## TODO: Add input type checking
    ## TODO: Add logging
    
    conv_type = "{}-to-{}".format(kbtype, etype)
    if conv_type  not in config or 'ws_id'  not in config[conv_type]['cmd_args'] or 'in_id'  not in config[conv_type]['cmd_args'] or 'output' not in config[conv_type]['cmd_args']:
        raise Exception("{} to {} conversion was not properly defined!".format(kbtype, etype))
    vcmd_lst = [config[conv_type]['cmd_name'], 
                config[conv_type]['cmd_args']['ws_id'], ws_id, 
                config[conv_type]['cmd_args']['in_id'], in_id, 
                config[conv_type]['cmd_args']['output'],"{}/{}".format(sdir,otmp)]

    if 'downloader' in opt_args:
        opt_args = opt_args['downloader']
        for k in opt_args:
            if k in config[etype]['opt_args']:
                vcmd_lst.append(config[etype]['opt_args'][k])
                vcmd_lst.append(opt_args[k])

    p1 = Popen(vcmd_lst, stdout=PIPE)
    out_str = p1.communicate()
    # print output message for error tracking
    if out_str[0] is not None : print out_str[0]
    if out_str[1] is not None : print >> sys.stderr, out_str[1]

    if p1.returncode != 0: 
        # TODO: add ujs status update here
        exit(p1.returncode) 
   

def upload_to_shock(surl, sdir, otmp):

    f = open('{}/{}'.format(sdir,otmp), 'rb')
    mfs = mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ)

    data_req = urllib2.Request("{}/node".format(surl, mfs))
    data_req.add_header('Authorization',"OAuth {}".format(os.environ.get('KB_AUTH_TOKEN')))
    data_req.add_header('Content-Type',"application/octet-stream")
    #data_req.add_header('Content-Disposition',"attachment;filename=")

    response = urllib2.urlopen(data_req)
    mfs.close()
    f.close()

    print response
        
if __name__ == "__main__":
    # Parse options.
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter, prog='trns_download_hndlr', epilog=desc3)
    parser.add_argument('-u', '--ws_url', help='Workspace url', action='store', dest='ws_url', default='https://kbase.us/services/ws')
    parser.add_argument('-x', '--svc_ws_name', help='Service workspace name', action='store', dest='sws_id', default=None, required=True)
    parser.add_argument('-c', '--config_name', help='Script configuration workspace object name', action='store', dest='cfg_name', default=None, required=True)

    parser.add_argument('-w', '--src_ws_name', help='Source workspace name', action='store', dest='ws_id', default=None, required=True)
    parser.add_argument('-i', '--in_id', help='Input workspace object name', action='store', dest='inobj_id', default=None, required=True)

    parser.add_argument('-s', '--shock_url', help='Shock url', action='store', dest='shock_url', default='https://kbase.us/services/shock-api')

    parser.add_argument('-e', '--ext_type', help='External object type', action='store', dest='etype', default=None, required=True)
    parser.add_argument('-t', '--kbase_type', help='KBase object type', action='store', dest='kbtype', default=None, required=True)

    parser.add_argument('-a', '--opt_args', help='Optional argument json string', action='store', dest='opt_args', default='{"downloader":{}}')
    parser.add_argument('-j', '--job_id', help='UJS job id', action='store', dest='jid', default=None, required=True)

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
#def download_handler (ws_url, cfg_name, sws_id, ws_id, in_id, etype, kbtype, sdir, otmp, opt_args, ujs_url, ujs_jid) :
    download_handler(args.ws_url, args.cfg_name, args.sws_id, args.ws_id, args.inobj_id, args.etype, args.kbtype, args.sdir, args.otmp, args.opt_args, "", args.jid)
    upload_to_shock(args.shock_url, args.sdir, args.otmp)

    # clean-up
    if(args.del_tmps is "true") :
        try :
          shutil.rmtree("{}".format(args.sdir))
        except:
          pass

    exit(0);
