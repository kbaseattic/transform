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

#
# TODO: Make the following function to be shared library function
#
def download_shock_data(surl, inobj_id, sdir, itmp) :
    # TODO: Improve folder checking
    try:
        os.mkdir(sdir)
    except:
        pass

    headers = {'Authorization' :  "OAuth {}".format(os.environ.get('KB_AUTH_TOKEN')) }

    data_req = urllib2.Request("{}/node/{}?download_raw".format(surl, inobj_id))
    data_req.add_header('Authorization',"OAuth {}".format(os.environ.get('KB_AUTH_TOKEN')))

    print "{}/node/{}?download_raw".format(surl, inobj_id)
    print os.environ.get('KB_AUTH_TOKEN')
    print "=============="

    data = urllib2.urlopen(data_req)
        
    
    dif = open("{}/{}".format(sdir, itmp),'w')
    dif.write(data.read())
    dif.close()
    data.close()


def validation_handler (args) :
    ###
    # download ws object and find where the validation script is located
    wsd = Workspace(url=args.ws_url, token=os.environ.get('KB_AUTH_TOKEN'))
    # TODO: get subobject
    config = wsd.get_object({'id' : args.cfg_name, 'workspace' : args.sws_id})['data']['config_map']

    if config is None:
        raise Exception("Object {} not found in workspace {}".format(args.etype, args.sws_id))
    
    ###
    # execute validation
    
    ## TODO: Add input type checking
    ## TODO: Add logging
    
    vcmd_lst = [config[args.etype]['cmd_name'], config[args.etype]['cmd_args']['input'], "{}/{}".format(args.sdir,args.itmp)]

    if 'validator' in args.opt_args:
      opt_args = args.opt_args['validator']
      for k in opt_args:
        if k in config[args.etype]['opt_args']:
          vcmd_lst.append(config[args.etype]['opt_args'][k])
          vcmd_lst.append(opt_args[k])
         
    p1 = Popen(vcmd_lst, stdout=PIPE)
    out_str = p1.communicate()
    # print output message for error tracking
    if out_str[0] is not None : print out_str[0]
    if out_str[1] is not None : print >> sys.stderr, out_str[1]


    if p1.returncode != 0: 
        # TODO: Update UJS job status and update log
        exit(p1.returncode) 

def transformation_handler (args) :
    ###
    # download ws object and find where the validation script is located
    wsd = Workspace(url=args.ws_url, token=os.environ.get('KB_AUTH_TOKEN'))
    # TODO: get subobject
    config = wsd.get_object({'id' : args.cfg_name, 'workspace' : args.sws_id})['data']['config_map']

    if config is None:
        raise Exception("Object {} not found in workspace {}".format(args.etype, args.sws_id))
    
    ###
    # execute validation
    
    ## TODO: Add input type checking
    ## TODO: Add logging
    
    conv_type = "{}-to-{}".format(args.etype, args.kbtype)
    vcmd_lst = [config[conv_type]['cmd_name'], config[conv_type]['cmd_args']['input'], "{}/{}".format(args.sdir,args.itmp), config[conv_type]['cmd_args']['output'],"{}/{}".format(args.sdir,args.otmp)]

    if 'transformer' in args.opt_args:
      opt_args = args.opt_args['transformer']
      for k in opt_args:
        if k in config[args.etype]['opt_args']:
          vcmd_lst.append(config[args.etype]['opt_args'][k])
          vcmd_lst.append(opt_args[k])

    p1 = Popen(vcmd_lst, stdout=PIPE)
    out_str = p1.communicate()
    # print output message for error tracking
    if out_str[0] is not None : print out_str[0]
    if out_str[1] is not None : print >> sys.stderr, out_str[1]

    if p1.returncode != 0: 
        # TODO: add ujs status update here
        exit(p1.returncode) 

def load_to_ws (args) :
    wsd = Workspace(url=args.ws_url, token=os.environ.get('KB_AUTH_TOKEN'))
    # TODO: Add input file checking
    jif = open("{}/{}".format(args.sdir,args.otmp, 'r'))
    data = json.loads(jif.read())
    jif.close()

    config = wsd.save_objects({'workspace':args.ws_id, 'objects' : [ {
      'type' : args.kbtype, 'data' : data, 'name' : args.outobj_id, 
      'meta' : { 'source_id' : args.inobj_id, 'source_type' : args.etype,
                 'ujs_job_id' : args.jid} } ]})

if __name__ == "__main__":
    # Parse options.
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter, prog='trnf_upload_handler', epilog=desc3)
    parser.add_argument('-u', '--ws_url', help='Workspace url', action='store', dest='ws_url', default='https://kbase.us/services/ws')
    parser.add_argument('-x', '--svc_ws_name', help='Service workspace name', action='store', dest='sws_id', default=None, required=True)
    parser.add_argument('-c', '--config_name', help='Script configuration workspace object name', action='store', dest='cfg_name', default=None, required=True)

    parser.add_argument('-s', '--shock_url', help='Shock url', action='store', dest='shock_url', default='https://kbase.us/services/shock-api')
    parser.add_argument('-i', '--in_id', help='Input Shock node id', action='store', dest='inobj_id', default=None, required=True)

    parser.add_argument('-w', '--dst_ws_name', help='Destination workspace name', action='store', dest='ws_id', default=None, required=True)
    parser.add_argument('-o', '--out_id', help='Output workspace object name', action='store', dest='outobj_id', default=None, required=True)

    parser.add_argument('-e', '--ext_type', help='External object type', action='store', dest='etype', default=None, required=True)
    parser.add_argument('-t', '--kbase_type', help='KBase object type', action='store', dest='kbtype', default=None, required=True)

    parser.add_argument('-a', '--opt_args', help='Optional argument json string', action='store', dest='opt_args', default='{"validator":{},"transformer":{}}')
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
    download_shock_data(args.shock_url, args.inobj_id, args.sdir, args.itmp)
    validation_handler(args)
    transformation_handler(args)
    load_to_ws(args)

    # clean-up
    if(args.del_tmps is "true") :
        try :
          shutil.rmtree("{}".format(args.sdir))
        except:
          pass

    exit(0);
