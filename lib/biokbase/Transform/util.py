#!/usr/bin/env python

import argparse
import sys
import os
import os.path
import io
import time
import datetime
import traceback
import ctypes
import subprocess
from subprocess import Popen, PIPE
import shutil 
from optparse import OptionParser
import requests
from requests_toolbelt import MultipartEncoder
import json
import magic
import gzip
import bz2
import tarfile
import zipfile
import glob
import ftplib
import re

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
        if(hasattr(args, 'otmp')):
          self.otmp = args.otmp
        else:
          self.otmp = "output"
        self.token = os.environ.get('KB_AUTH_TOKEN')
        
        if hasattr(args, 'ssl_verify'):
            self.ssl_verify = args.ssl_verify
        else:
            self.ssl_verify = True
            
        if hasattr(args, 'url_list'):
            self.url_list = args.url_list
        else:
            self.url_list = ["ftp://ftp.ncbi.nlm.nih.gov/genomes/refseq/bacteria/Bacillus_subtilis/reference/GCF_000009045.1_ASM904v1/GCF_000009045.1_ASM904v1_genomic.gbff.gz"]


    def upload_to_shock(self):
        if self.token is None:
            raise Exception("Unable to find token!")
        
        filePath = "{}/{}".format(self.sdir,self.otmp)
    
        #build the header
        header = dict()
        header["Authorization"] = "Oauth %s" % self.token

        dataFile = open(os.path.abspath(filePath))
        m = MultipartEncoder(fields={'upload': (os.path.split(filePath)[-1], dataFile)})
        header['Content-Type'] = m.content_type

        try:
            response = requests.post(self.shock_url + "/node", headers=header, data=m, allow_redirects=True, verify=self.ssl_verify)
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
    
    
    def download_from_urls(self, chunkSize=10 * 2**20):
        if self.token is None:
            raise Exception("Unable to find token!")
        
        if not os.path.exists(self.sdir):
            os.mkdir(self.sdir)
        elif not os.path.isdir(self.sdir):
            raise Exception("Attempting to process downloads using a path that is not a directory!")
    
        url_list = [x for x in self.inobj_id.split(",") if len(x.strip()) != 0]

        if len(url_list) == 0:
            raise Exception("No urls to upload from!")

        for url in url_list:
            data = None

            # detect url type
            if url.startswith("ftp://"):
                # check if file or directory
                host = url.split("ftp://")[1].split("/")[0]
                path = url.split("ftp://")[1].split("/", 1)[1]
            
                ftp_connection = ftplib.FTP(host)
                ftp_connection.login()
                file_list = ftp_connection.sendcmd("MLST {0}".format(path))
            
                if file_list.find("type=dir") > -1:
                    file_list = ftp_connection.nlst(path)
            
                if len(file_list) > 1:            
                    if len(file_list) > threshold:
                        raise Exception("Too many files to process, found so far {0:d}".format(len(file_list)))
                
                    dirname = path.split("/")[-1]
                
                    if len(dirname) == 0:
                        dirname = path.split("/")[-2]                
                
                    all_files = list()
                    check = file_list[:]
                    while len(check) > 0:
                        x = check.pop()
                
                        new_files = ftp_connection.nlst(x)
                    
                        for n in new_files:
                            details = ftp_connection.sendcmd("MLST {0}".format(n))
                            
                            if "type=file" in details:
                                all_files.append(n)
                            elif "type=dir" in details:
                                check.append(n)
                            if len(all_files) > threshold:
                                raise Exception("Too many files to process, found so far {0:d}".format(len(all_files)))
                    
                    os.mkdir(dirname)
            
                    for x in all_files:
                        with open(os.path.join(os.path.abspath(dirname), os.path.basename(x)), 'wb') as f:
                            print "Downloading {0}".format(host + x)
                            ftp_connection.retrbinary("RETR {0}".format(x), lambda s: f.write(s), 10 * 2**20)
                        extract_data(os.path.join(os.path.abspath(dirname), os.path.basename(x)))
                else:
                    with open(os.path.join(self.sdir, os.path.split(path)[-1]), 'wb') as f:
                        print "Downloading {0}".format(url)
                        ftp_connection.retrbinary("RETR {0}".format(path), lambda s: f.write(s), 10 * 2**20)  
                    extract_data(os.path.join(self.sdir, os.path.split(path)[-1]))
            
                ftp_connection.close()            
            elif url.startswith("http://") or url.startswith("https://"):
                print "Downloading {0}".format(url)

                download_url = None
                fileSize = 0
                fileName = None

                header = dict()
                header["Authorization"] = "Oauth %s" % self.token

                # check for a shock url
                try:
                    shock_id = re.search('^http[s]://.*/node/([a-fA-f0-9\-]+).*', url).group(1)
                except Exception, e:
                    shock_id = None

                if shock_id is None:
                    print >> sys.stderr, "Downloading non-shock data"

                    download_url = url
                    fileName = url.split('/')[-1]
                else:
                    print >> sys.stderr, "Downloading shock node"

                    metadata_response = requests.get("{0}/node/{1}?verbosity=metadata".format(self.shock_url, shock_id), headers=header, stream=True, verify=self.ssl_verify)
                    shock_metadata = metadata_response.json()['data']
                    fileName = shock_metadata['file']['name']
                    fileSize = shock_metadata['file']['size']
                    metadata_response.close()
                        
                    download_url = "{0}/node/{1}?download_raw".format(self.shock_url, shock_id)
                    
                data = requests.get(download_url, headers=header, stream=True, verify=self.ssl_verify)
                size = int(data.headers['content-length'])

                if size > 0 and fileSize == 0:
                    fileSize = size
                
                filePath = os.path.join(self.sdir, fileName)
        
                f = io.open(filePath, 'wb')
                try:
                    for chunk in data.iter_content(chunkSize):
                        f.write(chunk)
                finally:
                    data.close()
                    f.close()      
                
                self.extract_data(filePath)
            else:
                raise Exception("Unrecognized protocol or url format : " + url)
            
        
    def extract_data(self, filePath, chunkSize=10 * 2**20):
        def extract_tar(tarPath):
            if not tarfile.is_tarfile(tarPath):
                raise Exception("Inavalid tar file " + tarPath)
        
            with tarfile.open(tarPath, 'r') as tarDataFile:
                memberlist = tarDataFile.getmembers()
            
                for member in memberlist:
                    memberPath = os.path.join(os.path.dirname(os.path.abspath(tarPath)),os.path.basename(os.path.abspath(member.name)))
            
                    if member.isfile():
                        with open(memberPath, 'wb') as f:
                            inputFile = tarDataFile.extractfile(member.name)
                            f.write(inputFile.read(chunkSize))
        
            os.remove(tarPath)

        mimeType = None    
        with magic.Magic(flags=magic.MAGIC_MIME_TYPE) as m:
            mimeType = m.id_filename(filePath)

        print "Extracting {0} as {1}".format(filePath, mimeType)

        if mimeType == "application/x-gzip":
            outFile = os.path.splitext(filePath)[0]
            with gzip.GzipFile(filePath, 'rb') as gzipDataFile, open(outFile, 'wb') as f:
                for chunk in gzipDataFile:
                    f.write(chunk)
            
            os.remove(filePath)
            outPath = os.path.dirname(filePath)

            # check for tar        
            with magic.Magic(flags=magic.MAGIC_MIME_TYPE) as m:
                mimeType = m.id_filename(outFile)

            if mimeType == "application/x-tar":
                print "Extracting {0} as tar".format(outFile)
                extract_tar(outFile)
        elif mimeType == "application/x-bzip2":
            outFile = os.path.splitext(filePath)[0]
            with bz2.BZ2File(filePath, 'r') as bz2DataFile, open(outFile, 'wb') as f:
                for chunk in bz2DataFile:
                    f.write(chunk)
            
            os.remove(filePath)
            outPath = os.path.dirname(filePath)

            # check for tar        
            with magic.Magic(flags=magic.MAGIC_MIME_TYPE) as m:
                mimeType = m.id_filename(outFile)

            if mimeType == "application/x-tar":
                print "Extracting {0} as tar".format(outFile)
                extract_tar(outFile)
        elif mimeType == "application/zip":
            if not zipfile.is_zipfile(filePath):
                raise Exception("Invalid zip file!")                
            
            outPath = os.path.dirname(filePath)
            
            with zipfile.ZipFile(filePath, 'r') as zipDataFile:
                bad = zipDataFile.testzip()
            
                if bad is not None:
                    raise Exception("Encountered a bad file in the zip : " + str(bad))
            
                infolist = zipDataFile.infolist()
            
                # perform sanity check on file names, extract each file individually
                for x in infolist:
                    infoPath = os.path.join(outPath, os.path.basename(os.path.abspath(x.filename)))
                    
                    if not os.path.exists(os.path.dirname(infoPath)):
                        os.makedirs(infoPath)                    
                    
                    if os.path.exists(os.path.join(infoPath,os.path.split(x.filename)[-1])):
                        raise Exception("Extracting zip contents will overwrite an existing file!")
                    
                    with open(infoPath, 'wb') as f:
                        f.write(zipDataFile.read(x.filename))
            
            os.remove(filePath)
        elif mimeType == "application/x-gtar":
            if not tarfile.is_tarfile(filePath):
                raise Exception("Inavalid tar file " + filePath)

            outPath = os.path.dirname(filePath)

            with tarfile.open(filePath, 'r|*') as tarDataFile:
                memberlist = tarDataFile.getmembers()
    
                # perform sanity check on file names, extract each file individually
                for member in memberlist:
                    memberPath = os.path.join(outPath, os.path.basename(os.path.abspath(member.name)))

                    if os.path.exists(os.path.dirname(infoPath)):
                        os.makedirs(infoPath)                    

                    if os.path.exists(os.path.join(infoPath,os.path.split(member.name)[-1])):
                        raise Exception("Extracting zip contents will overwrite an existing file!")
    
                    if member.isfile():
                        with open(memberPath, 'wb') as f, tarDataFile.extractfile(member.name) as inputFile:
                            f.write(inputFile.read(chunkSize))

            os.remove(filePath)



class Validator(TransformBase):
    def __init__(self, args):
        TransformBase.__init__(self,args)
        self.ws_url = args.ws_url
        self.etype = args.etype
        self.opt_args = args.opt_args

        print >> sys.stderr, args

        
        self.config = args.job_details

        # download ws object and find where the validation script is located
        #self.wsd = Workspace(url=self.ws_url, token=self.token)
        #self.config = self.wsd.get_object({'id' : self.cfg_name, 'workspace' : self.sws_id})['data']['config_map']
        
        #if self.config is None:
        #    raise Exception("Object {} not found in workspace {}".format(self.cfg_name, self.sws_id))


    def validation_handler (self) :
        ###
        # execute validation
        ## TODO: Add logging

        print >> sys.stderr, self.config
        
        if 'validator' not in self.config:
            raise Exception("No validation script was registered for {}".format(self.etype))

        fd_list = []
        if os.path.exists("{}/{}".format(self.sdir,self.itmp)):
            fd_list.append( "{}/{}".format(self.sdir,self.itmp))
        else:
            fd_list = glob.glob("{}/{}_*".format(self.sdir,self.itmp))

        for fd in fd_list:
            vcmd_lst = [self.config['validator']['cmd_name'], self.config['validator']['cmd_args']['input'], fd]
         
        #if 'validator' in self.opt_args:
        #    opt_args = self.opt_args['validator']
        #    for k in opt_args:
        #        if k in self.config['validator'][self.etype]['opt_args'] and opt_args[k] is not None:
        #            vcmd_lst.append(self.config['validator'][self.etype]['opt_args'][k])
        #            vcmd_lst.append(opt_args[k])
               
            p1 = Popen(vcmd_lst, stdout=PIPE)
            out_str = p1.communicate()
          
            # print output message for error tracking
            if out_str[0] is not None:
                print out_str[0]
            if out_str[1] is not None:
                print >> sys.stderr, out_str[1]
         
            if p1.returncode != 0: 
                raise Exception(out_str[1])

class Uploader(Validator):
    def __init__(self, args):
        Validator.__init__(self, args)
        self.kbtype = args.kbtype
        self.ws_id = args.ws_id
        self.outobj_id = args.outobj_id
        self.jid = args.jid
        self.otmp = args.otmp


    def transformation_handler (self) :
        conv_type = "{}-to-{}".format(self.etype, self.kbtype)

        if 'transformer' not in self.config:
            raise Exception("No conversion script was registered for {}".format(conv_type))
        
        vcmd_lst = [self.config['transformer']['cmd_name']]
        vcmd_lst.append(self.config['transformer']['cmd_args']['input'])
        if 'cmd_args_override' in self.config['transformer'] and 'input' in self.config['transformer']['cmd_args_override']:
            if self.config['transformer']['cmd_args_override']['input'] == 'shock_node_id': # use shock node id
                vcmd_lst.append(self.inobj_id)
            else:
                vcmd_lst.append("{}/{}".format(self.sdir,self.itmp)) # not defined yet
        else:
            vcmd_lst.append("{}/{}".format(self.sdir,self.itmp)) # default input is the input file or folder

        vcmd_lst.append(self.config['transformer']['cmd_args']['output'])
        if 'cmd_args_override' in self.config['transformer'] and 'output' in self.config['transformer']['cmd_args_override']:
            vcmd_lst.append("{}/{}".format(self.sdir,self.otmp)) # not defined yet
        else: 
            vcmd_lst.append("{}/{}".format(self.sdir,self.otmp))
    
        #if 'transformer' in self.opt_args:
        #  opt_args = self.opt_args['transformer']
        #  for k in opt_args:
        #    if k in self.config['transformer'][conv_type]['opt_args'] and opt_args[k] is not None:
        #      vcmd_lst.append(self.config['transformer'][conv_type]['opt_args'][k])
        #      vcmd_lst.append(opt_args[k])
    
        p1 = Popen(vcmd_lst, stdout=PIPE)
        out_str = p1.communicate()
        # print output message for error tracking
        if out_str[0] is not None : print out_str[0]
        if out_str[1] is not None : print >> sys.stderr, out_str[1]
    
        if p1.returncode != 0: 
            raise Exception(out_str[1])

    def upload_handler (self) :

        print >> sys.stderr, self.config
        
        if 'uploader' in self.config: # upload handler is registered
            vcmd_lst = [self.config['uploader']['cmd_name'], 
                      self.config['uploader']['cmd_args']['ws_url'],
                      self.ws_url,
                      self.config['uploader']['cmd_args']['ws_id'],
                      self.ws_id,
                      self.config['uploader']['cmd_args']['outobj_id'],
                      self.outobj_id,
                      self.config['uploader']['cmd_args']['dir'],
                      self.sdir]
         
            #if 'uploader' in self.opt_args:
            #  opt_args = self.opt_args['uploader']
            #  for k in opt_args:
            #      if k in self.config['uploader']['opt_args'] and opt_args[k] is not None:
            #          vcmd_lst.append(self.config['uploader']['opt_args'][k])
            #          vcmd_lst.append(opt_args[k])

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
        print >> sys.stderr, self.sdir
        print >> sys.stderr, self.otmp

        jif = open("{}/{}".format(self.sdir,self.otmp, 'r'))
        data = json.loads(jif.read())
        jif.close()
    
        print >> sys.stderr, self.data

        self.wsd.save_objects({'workspace':self.ws_id, 'objects' : [ {
          'type' : self.kbtype, 'data' : data, 'name' : self.outobj_id, 
          'meta' : { 'source_id' : self.inobj_id, 'source_type' : self.etype,
                     'ujs_job_id' : self.jid} } ]})


class Downloader(TransformBase):
    def __init__(self, args):
        TransformBase.__init__(self,args)
        self.ws_url = args.ws_url
        self.etype = args.etype
        self.opt_args = args.opt_args
        self.kbtype = args.kbtype
        #self.otmp = args.otmp
        self.ws_id = args.ws_id
        #self.outobj_id = args.outobj_id
        self.jid = args.jid
        self.compress = args.compress

        # download ws object and find where the validation script is located
        #self.wsd = Workspace(url=self.ws_url, token=self.token)
        #self.config = self.wsd.get_object({'id' : self.cfg_name, 'workspace' : self.sws_id})['data']['config_map']
     
        self.config = args.job_details
        #if self.config is None:
        #    raise Exception("Object {} not found in workspace {}".format(self.cfg_name, self.sws_id))
    
    def download_ws_data (self) :
        try:
            os.mkdir(self.sdir)
        except:
            pass
    
        dif = open("{}/{}".format(self.sdir, "{}".format(self.itmp)),'w')
        data = self.wsd.get_object({'id' : self.inobj_id, 'workspace' : self.ws_id})['data']
        json.dump(data,dif)
        dif.close()


    #def download_handler (ws_url, cfg_name, sws_id, ws_id, in_id, etype, kbtype, sdir, otmp, opt_args, ujs_url, ujs_jid) :
    def download_handler (self) :
        try:
            os.mkdir(self.sdir)
        except:
            pass
    
        conv_type = "{}-to-{}".format(self.kbtype, self.etype)
        if conv_type  not in self.config['down_transformer'] or 'inobj_id'  not in self.config['down_transformer'][conv_type]['cmd_args'] or 'ws_id'  not in self.config['down_transformer'][conv_type]['cmd_args'] or 'output'  not in self.config['down_transformer'][conv_type]['cmd_args']:
            raise Exception("{} to {} conversion was not properly defined!".format(self.kbtype, self.etype))
        vcmd_lst = [self.config['down_transformer'][conv_type]['cmd_name'], 
                    self.config['down_transformer'][conv_type]['cmd_args']['ws_id'], self.ws_id, 
                    self.config['down_transformer'][conv_type]['cmd_args']['inobj_id'], self.inobj_id, 
                    self.config['down_transformer'][conv_type]['cmd_args']['output'],"{}/{}".format(self.sdir,self.otmp)]
    
        if 'down_transformer' in self.opt_args:
            opt_args = self.opt_args['down_transformer']
            for k in opt_args:
                if k in self.config['down_transformer'][conv_type]['opt_args'] and opt_args[k] is not None:
                    vcmd_lst.append(self.config['down_transformer'][conv_type]['opt_args'][k])
                    vcmd_lst.append(opt_args[k])
    
        p1 = Popen(vcmd_lst, stdout=PIPE)
        out_str = p1.communicate()

        if out_str[0] is not None : print out_str[0]
        if out_str[1] is not None : print >> sys.stderr, out_str[1]
    
        if p1.returncode != 0: 
            raise Exception(out_str[1])

        cf = self.compress;
        cf = 'bztar' if(self.compress == 'bz2')
        if(cf != "none"):
          shutil.make_archive("{}/{}".format(self.sdir,self.otmp),cf)
          self.otmp = "%s.zip" % self.otmp if cf == "zip"
          self.otmp = "%s.tar.gz2" % self.otmp if cf == "bz2"
