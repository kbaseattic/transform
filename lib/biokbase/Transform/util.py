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


# Base class for Transform service
class TransformBase:

    def __init__(self, args):
        self.shock_url = args.shock_url
        self.inobj_id = args.inobj_id
        self.sdir = args.sdir
        self.itmp = args.itmp
        self.token = os.environ.get('KB_AUTH_TOKEN')

    def download_shock_data_args(self, shock_url, inobj_id, sdir, itmp) : # python 2.7 does not support method overloading
        # TODO: Improve folder checking
        try:
            os.mkdir(sdir)
        except:
            pass
    
        #headers = {'Authorization' :  "OAuth {}".format(os.environ.get('KB_AUTH_TOKEN')) }
    
        meta_req = urllib2.Request("{}/node/{}".format(shock_url, inobj_id))
        meta_req.add_header('Authorization',"OAuth {}".format(self.token))
        data_req = urllib2.Request("{}/node/{}?download_raw".format(shock_url, inobj_id))
        data_req.add_header('Authorization',"OAuth {}".format(self.token))
    
        meta = urllib2.urlopen(meta_req)
        md = json.loads(meta.read())
        meta.close()
        print md
    
        data = urllib2.urlopen(data_req)
            
        dif = open("{}/{}".format(sdir, itmp),'w')
        dif.write(data.read())
        dif.close()
        data.close()

    def download_shock_data(self) :
        # TODO: Improve folder checking
        try:
            os.mkdir(self.sdir)
        except:
            pass
    
        #headers = {'Authorization' :  "OAuth {}".format(os.environ.get('KB_AUTH_TOKEN')) }
    
        meta_req = urllib2.Request("{}/node/{}".format(self.shock_url, self.inobj_id))
        meta_req.add_header('Authorization',"OAuth {}".format(self.token))
        data_req = urllib2.Request("{}/node/{}?download_raw".format(self.shock_url, self.inobj_id))
        data_req.add_header('Authorization',"OAuth {}".format(self.token))
    
        meta = urllib2.urlopen(meta_req)
        md = json.loads(meta.read())
        meta.close()
        print md
    
        data = urllib2.urlopen(data_req)
            
        dif = open("{}/{}".format(self.sdir, self.itmp),'w')
        dif.write(data.read())
        dif.close()
        data.close()



class Validator(TransformBase):
    def __init__(self, args):
        TransformBase.__init__(self,args)
        self.ws_url = args.ws_url
        self.cfg_name = args.cfg_name
        self.sws_id = args.sws_id
        self.etype = args.etype
        self.opt_args = args.opt_args

        # download ws object and find where the validation script is located
        self.wsd = Workspace(url=self.ws_url, token=self.token)
        self.config = self.wsd.get_object({'id' : self.cfg_name, 'workspace' : self.sws_id})['data']['config_map']
     
        if self.config is None:
            raise Exception("Object {} not found in workspace {}".format(self.cfg_name, self.sws_id))


    def validation_handler_args (self, etype, sdir, itmp, opt_args) :
        ###
        # execute validation
        ## TODO: Add logging
        
        if etype not in self.config:
          raise Exception("No validation script was registered for {}".format(etype))

        vcmd_lst = [self.config[etype]['cmd_name'], self.config[etype]['cmd_args']['input'], "{}/{}".format(sdir,itmp)]
    
        if 'validator' in opt_args:
          opt_args = opt_args['validator']
          for k in opt_args:
            if k in self.config[etype]['opt_args']:
              vcmd_lst.append(self.config[etype]['opt_args'][k])
              vcmd_lst.append(opt_args[k])
             
        p1 = Popen(vcmd_lst, stdout=PIPE)
        out_str = p1.communicate()
        # print output message for error tracking
        if out_str[0] is not None : print out_str[0]
        if out_str[1] is not None : print >> sys.stderr, out_str[1]
    
        if p1.returncode != 0: 
            raise Exception(out_str[1])

    def validation_handler (self) :
        ###
        # execute validation
        ## TODO: Add logging
        
        if self.etype not in self.config:
          raise Exception("No validation script was registered for {}".format(self.etype))

        vcmd_lst = [self.config[self.etype]['cmd_name'], self.config[self.etype]['cmd_args']['input'], "{}/{}".format(self.sdir,self.itmp)]
    
        if 'validator' in self.opt_args:
          opt_args = self.opt_args['validator']
          for k in opt_args:
            if k in self.config[etype]['opt_args']:
              vcmd_lst.append(self.config[self.etype]['opt_args'][k])
              vcmd_lst.append(opt_args[k])
             
        p1 = Popen(vcmd_lst, stdout=PIPE)
        out_str = p1.communicate()
        # print output message for error tracking
        if out_str[0] is not None : print out_str[0]
        if out_str[1] is not None : print >> sys.stderr, out_str[1]
    
        if p1.returncode != 0: 
            raise Exception(out_str[1])

class Uploader(Validator):
    def __init__(self, args):
        Validator.__init__(self, args)
        self.kbtype = args.kbtype
        self.otmp = args.otmp
        self.ws_id = args.ws_id
        self.outobj_id = args.outobj_id
        self.jid = args.jid

    def transformation_handler_args (self, etype, kbtype, sdir, itmp, otmp, opt_args) :
        conv_type = "{}-to-{}".format(etype, kbtype)
        vcmd_lst = [self.config[conv_type]['cmd_name'], self.config[conv_type]['cmd_args']['input'], "{}/{}".format(sdir,itmp), self.config[conv_type]['cmd_args']['output'],"{}/{}".format(sdir,otmp)]
    
        if 'transformer' in opt_args:
          opt_args = opt_args['transformer']
          for k in opt_args:
            if k in self.config[conv_type]['opt_args']:
              vcmd_lst.append(self.config[conv_type]['opt_args'][k])
              vcmd_lst.append(opt_args[k])
    
        p1 = Popen(vcmd_lst, stdout=PIPE)
        out_str = p1.communicate()
        # print output message for error tracking
        if out_str[0] is not None : print out_str[0]
        if out_str[1] is not None : print >> sys.stderr, out_str[1]
    
        if p1.returncode != 0: 
                raise Exception(out_str[1])

    def transformation_handler (self) :
        conv_type = "{}-to-{}".format(self.etype, self.kbtype)
        vcmd_lst = [self.config[conv_type]['cmd_name'], self.config[conv_type]['cmd_args']['input'], "{}/{}".format(self.sdir,self.itmp), self.config[conv_type]['cmd_args']['output'],"{}/{}".format(self.sdir,self.otmp)]
    
        if 'transformer' in self.opt_args:
          opt_args = self.opt_args['transformer']
          for k in opt_args:
            if k in self.config[conv_type]['opt_args']:
              vcmd_lst.append(self.config[conv_type]['opt_args'][k])
              vcmd_lst.append(opt_args[k])
    
        p1 = Popen(vcmd_lst, stdout=PIPE)
        out_str = p1.communicate()
        # print output message for error tracking
        if out_str[0] is not None : print out_str[0]
        if out_str[1] is not None : print >> sys.stderr, out_str[1]
    
        if p1.returncode != 0: 
                raise Exception(out_str[1])

    def upload_handler_args (self, ws_url, cfg_name, sws_id, etype, kbtype, sdir, otmp, ws_id, obj_id, opt_args, jid) :
        
        if kbtype in self.config: # upload handler is registered
          vcmd_lst = [self.config[kbtype]['cmd_name'], self.config[kbtype]['cmd_args']['ws_url'], self.ws_url, self.config[kbtype]['cmd_args']['ws_id'], ws_id, self.config[kbtype]['cmd_args']['outobj_id'], outobj_id,  self.config[kbtype]['cmd_args']['dir'], sdir ]
         
          if 'uploader' in opt_args:
            opt_args = opt_args['uploader']
            for k in opt_args:
              if k in self.config[kbtype]['opt_args']:
                vcmd_lst.append(self.config[kbtype]['opt_args'][k])
                vcmd_lst.append(opt_args[k])
         
          p1 = Popen(vcmd_lst, stdout=PIPE)
          out_str = p1.communicate()
          # print output message for error tracking
          if out_str[0] is not None : print out_str[0]
          if out_str[1] is not None : print >> sys.stderr, out_str[1]
         
          if p1.returncode != 0: 
              raise Exception(out_str[1])
        else: # upload handler was not registered
          self.upload_to_ws_args(sdir,otmp,ws_id,kbtype,outobj_id,inobj_id,etype,jid) # use default WS uploader
    
    def upload_handler (self) :
        
        if self.kbtype in self.config: # upload handler is registered
          vcmd_lst = [self.config[self.kbtype]['cmd_name'], self.config[self.kbtype]['cmd_args']['ws_url'], self.ws_url, self.config[self.kbtype]['cmd_args']['ws_id'], self.ws_id, self.config[self.kbtype]['cmd_args']['outobj_id'], self.outobj_id,  self.config[self.kbtype]['cmd_args']['dir'], self.sdir ]
         
          if 'uploader' in self.opt_args:
            opt_args = self.opt_args['uploader']
            for k in opt_args:
              if k in self.config[self.kbtype]['opt_args']:
                vcmd_lst.append(self.config[self.kbtype]['opt_args'][k])
                vcmd_lst.append(opt_args[k])
         
          p1 = Popen(vcmd_lst, stdout=PIPE)
          out_str = p1.communicate()
          # print output message for error tracking
          if out_str[0] is not None : print out_str[0]
          if out_str[1] is not None : print >> sys.stderr, out_str[1]
         
          if p1.returncode != 0: 
              raise Exception(out_str[1])
        else: # upload handler was not registered
          self.upload_to_ws() # use default WS uploader
    
    def upload_to_ws_args (self, sdir,otmp,ws_id,kbtype,outobj_id,inobj_id,etype,jid) :
        jif = open("{}/{}".format(sdir,otmp, 'r'))
        data = json.loads(jif.read())
        jif.close()
    
        self.wsd.save_objects({'workspace':ws_id, 'objects' : [ {
          'type' : kbtype, 'data' : data, 'name' : outobj_id, 
          'meta' : { 'source_id' : inobj_id, 'source_type' : etype,
                     'ujs_job_id' : jid} } ]})

    def upload_to_ws (self) :
        jif = open("{}/{}".format(self.sdir,self.otmp, 'r'))
        data = json.loads(jif.read())
        jif.close()
    
        self.wsd.save_objects({'workspace':self.ws_id, 'objects' : [ {
          'type' : self.kbtype, 'data' : data, 'name' : self.outobj_id, 
          'meta' : { 'source_id' : self.inobj_id, 'source_type' : self.etype,
                     'ujs_job_id' : self.jid} } ]})
