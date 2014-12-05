#!/usr/bin/python
import argparse
import sys
import os
import os.path
import io
import time
import traceback
import ctypes
import subprocess
from subprocess import Popen, PIPE
import shutil
from optparse import OptionParser
import requests
from requests_toolbelt import MulitpartEncoder
import urllib
import urllib2
import json
import tarfile
import zipfile
import glob

try:
    from cStringIO import StringIO
except:
    from StringIO import StringIO


from biokbase.workspace.client import Workspace



BUF_SIZE = 8*1024 # default HTTP LIB client buffer_size

# Base class for Transform service
class TransformBase:

    def __init__(self, args):
        self.shock_url = args.shock_url
        self.inobj_id = args.inobj_id
        self.sdir = args.sdir
        self.itmp = args.itmp
        self.token = os.environ.get('KB_AUTH_TOKEN')
        self.ssl_verify = True


    def upload_to_shock(self, filePath):
        if self.token is None:
            raise Exception("Unable to find token!")
    
        #build the header
        header = dict()
        header["Authorization"] = "Oauth %s" % token

        dataFile = open(os.path.abspath(filePath))
        m = MultipartEncoder(fields={'upload': (os.path.split(filePath)[-1], dataFile)})
        header['Content-Type'] = m.content_type

        try:
            response = requests.post(self.shock_url + "/node", headers=header, data=m, allow_redirects=True, verify=ssl_verify)
            dataFile.close()
    
            if not response.ok:
                response.raise_for_status()

            result = response.json()

            if result['error']:
                raise Exception(result['error'][0])
            else:
                return result["data"]    
        except:
            dataFile.close()
            raise
    
    
    def download_shock_data(self) :
        # TODO: Improve folder checking
        try:
            os.mkdir(self.sdir)
        except:
            pass
    
        inids = self.inobj_id.split(',')
    
        for i in range(len(inids)):
            meta_req = urllib2.Request("{}/node/{}".format(self.shock_url, inids[i]))
            meta_req.add_header('Authorization',"OAuth {}".format(self.token))
            data_req = urllib2.Request("{}/node/{}?download_raw".format(self.shock_url, inids[i]))
            data_req.add_header('Authorization',"OAuth {}".format(self.token))
      
            meta = urllib2.urlopen(meta_req)
            md = json.loads(meta.read())
            meta.close()
      
            rdata = urllib2.urlopen(data_req)
 
            data = StringIO(rdata.read())
            magic = data.read(4)
            data.seek(0)
          
            if magic.startswith('\x1f\x8b') or magic.startswith('\x42\x5a') : # gz or bz
                my_tar = tarfile.open(fileobj=data, mode="r|*", bufsize=BUF_SIZE) 
                if len(inids) > 1 :
                    my_tar.extractall(path="{}/{}".format(self.sdir, "{}_{}".format(self.itmp,i)))
                else:
                    my_tar.extractall(path="{}/{}".format(self.sdir, self.itmp))
                my_tar.close()
            elif magic == '\x50\x4b\x03\x04': # zip
                my_zip = zipfile.ZipFile(data, mode="r")
                if len(inids) > 1 :
                    my_zip.extractall(path="{}/{}".format(self.sdir, "{}_{}".format(self.itmp,i)))
                else:
                    my_zip.extractall(path="{}/{}".format(self.sdir, self.itmp))
                my_zip.close()
            else:  
                if len(inids) > 1 :
                    dif = open("{}/{}".format(self.sdir, "{}_{}".format(self.itmp,i)),'w')
                else:
                    dif = open("{}/{}".format(self.sdir, self.itmp),'w')
                dif.write(data.read())
                dif.close()
            rdata.close()
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


    def validation_handler (self) :
        ###
        # execute validation
        ## TODO: Add logging
        
        if self.etype not in self.config['validator']:
          raise Exception("No validation script was registered for {}".format(self.etype))

        fd_list = []
        if os.path.exists("{}/{}".format(self.sdir,self.itmp)):
          fd_list.append( "{}/{}".format(self.sdir,self.itmp))
        else:
          fd_list = glob.glob("{}/{}_*".format(self.sdir,self.itmp))

        for fd in fd_list:
          vcmd_lst = [self.config['validator'][self.etype]['cmd_name'], self.config['validator'][self.etype]['cmd_args']['input'], fd]
         
          if 'validator' in self.opt_args:
            opt_args = self.opt_args['validator']
            for k in opt_args:
              if k in self.config['validator'][etype]['opt_args'] and opt_args[k] is not None:
                vcmd_lst.append(self.config['validator'][self.etype]['opt_args'][k])
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


    def transformation_handler (self) :
        conv_type = "{}-to-{}".format(self.etype, self.kbtype)

        if conv_type not in self.config['transformer']:
          raise Exception("No conversion script was registered for {}".format(conv_type))
        vcmd_lst = [self.config['transformer'][conv_type]['cmd_name']]
        vcmd_lst.append(self.config['transformer'][conv_type]['cmd_args']['input'])
        if 'cmd_args_override' in self.config['transformer'][conv_type] and 'input' in self.config['transformer'][conv_type]['cmd_args_override']:
          if self.config['transformer'][conv_type]['cmd_args_override']['input'] == 'shock_node_id': # use shock node id
            vcmd_lst.append(self.inobj_id)
          else: vcmd_lst.append("{}/{}".format(self.sdir,self.itmp)) # not defined yet
        else: vcmd_lst.append("{}/{}".format(self.sdir,self.itmp)) # default input is the input file or folder

        vcmd_lst.append(self.config['transformer'][conv_type]['cmd_args']['output'])
        if 'cmd_args_override' in self.config['transformer'][conv_type] and 'output' in self.config['transformer'][conv_type]['cmd_args_override']:
          vcmd_lst.append("{}/{}".format(self.sdir,self.otmp)) # not defined yet
        else: vcmd_lst.append("{}/{}".format(self.sdir,self.otmp))
    
        if 'transformer' in self.opt_args:
          opt_args = self.opt_args['transformer']
          for k in opt_args:
            if k in self.config['transformer'][conv_type]['opt_args'] and opt_args[k] is not None:
              vcmd_lst.append(self.config['transformer'][conv_type]['opt_args'][k])
              vcmd_lst.append(opt_args[k])
    
        p1 = Popen(vcmd_lst, stdout=PIPE)
        out_str = p1.communicate()
        # print output message for error tracking
        if out_str[0] is not None : print out_str[0]
        if out_str[1] is not None : print >> sys.stderr, out_str[1]
    
        if p1.returncode != 0: 
                raise Exception(out_str[1])

    def upload_handler (self) :
        
        if self.kbtype in self.config['uploader']: # upload handler is registered
          vcmd_lst = [self.config['uploader'][self.kbtype]['cmd_name'], self.config['uploader'][self.kbtype]['cmd_args']['ws_url'], self.ws_url, self.config['uploader'][self.kbtype]['cmd_args']['ws_id'], self.ws_id, self.config['uploader'][self.kbtype]['cmd_args']['outobj_id'], self.outobj_id,  self.config['uploader'][self.kbtype]['cmd_args']['dir'], self.sdir ]
         
          if 'uploader' in self.opt_args:
            opt_args = self.opt_args['uploader']
            for k in opt_args:
              if k in self.config['uploader'][self.kbtype]['opt_args'] and opt_args[k] is not None:
                vcmd_lst.append(self.config['uploader'][self.kbtype]['opt_args'][k])
                vcmd_lst.append(opt_args[k])

          print vcmd_lst

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
