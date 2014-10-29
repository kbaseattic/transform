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

def download_shock_data(surl, inobj_id, sdir, itmp) :
    # TODO: Improve folder checking
    try:
        os.mkdir(sdir)
    except:
        pass

    headers = {'Authorization' :  "OAuth {}".format(os.environ.get('KB_AUTH_TOKEN')) }

    data_req = urllib2.Request("{}/node/{}?download_raw".format(surl, inobj_id))
    data_req.add_header('Authorization',"OAuth {}".format(os.environ.get('KB_AUTH_TOKEN')))

    data = urllib2.urlopen(data_req)
        
    dif = open("{}/{}".format(sdir, itmp),'w')
    dif.write(data.read())
    dif.close()
    data.close()


def validation_handler (ws_url, cfg_name, sws_id, etype, sdir, itmp, opt_args, ujs_url, ujs_jid) :
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
    
    vcmd_lst = [config[etype]['cmd_name'], config[etype]['cmd_args']['input'], "{}/{}".format(sdir,itmp)]

    if 'validator' in opt_args:
      opt_args = opt_args['validator']
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
        # TODO: Update UJS job status and update log
        exit(p1.returncode) 

def transformation_handler (ws_url, cfg_name, sws_id, etype, kbtype, sdir, itmp, otmp, opt_args, ujs_url, ujs_jid) :
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
    
    conv_type = "{}-to-{}".format(etype, kbtype)
    vcmd_lst = [config[conv_type]['cmd_name'], config[conv_type]['cmd_args']['input'], "{}/{}".format(sdir,itmp), config[conv_type]['cmd_args']['output'],"{}/{}".format(sdir,otmp)]

    if 'transformer' in opt_args:
      opt_args = opt_args['transformer']
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

def upload_to_ws (ws_url,sdir,otmp,ws_id,kbtype,outobj_id,inobj_id,etype,jid) :
    wsd = Workspace(url=ws_url, token=os.environ.get('KB_AUTH_TOKEN'))
    # TODO: Add input file checking
    jif = open("{}/{}".format(sdir,otmp, 'r'))
    data = json.loads(jif.read())
    jif.close()

    config = wsd.save_objects({'workspace':ws_id, 'objects' : [ {
      'type' : kbtype, 'data' : data, 'name' : outobj_id, 
      'meta' : { 'source_id' : inobj_id, 'source_type' : etype,
                 'ujs_job_id' : jid} } ]})
