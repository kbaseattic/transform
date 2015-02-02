#!/usr/bin/env python

import sys
import time
import datetime
import os
import os.path
import io
import bz2
import gzip
import zipfile
import tarfile
import json
import pprint
import subprocess

# patch for handling unverified certificates
import ssl
if hasattr(ssl, '_create_unverified_context'):
    ssl._create_default_https_context = ssl._create_unverified_context

try:
    from requests_toolbelt import MultipartEncoder, MultipartEncoderMonitor
    import requests
    import magic
    import blessings
    import dateutil.parser
    import dateutil.tz

    import biokbase.Transform.Client
    import biokbase.Transform.script_utils
    import biokbase.Transform.handler_utils
    import biokbase.userandjobstate.client
    import biokbase.workspace.client

    try:
        from biokbase.HandleService.Client import HandleService as HandleClient
    except:
        from biokbase.AbstractHandle.Client import AbstractHandle as HandleClient
except ImportError, e:
    raise ImportError("Your environment is not setup correctly : {0}".format(e.message))



class TransformDriver(object):
    def __init__(self, service_urls=dict(), logger=biokbase.Transform.script_utils.stdoutlogger(__file__)):        
        self.logger = logger
        
        if self.logger is None:
            raise Exception("The logger instance you provided appears to be None.")
        
        logger.info("Instantiating Transform Client Driver")
        
        self.token = biokbase.Transform.script_utils.get_token()
        
        # create all service clients
        if service_urls.has_key("transform_service_url"):        
            self.transform_client = biokbase.Transform.Client.Transform(url=service_urls["transform_service_url"], token=self.token)
        else:
            raise Exception("Missing transform_service_url")

        if service_urls.has_key("ujs_service_url"):        
            self.ujs_client = biokbase.userandjobstate.client.UserAndJobState(url=service_urls["ujs_service_url"], token=self.token)
        else:
            raise Exception("Missing ujs_service_url")

        if service_urls.has_key("awe_service_url"):
            self.awe_service_url = service_urls["awe_service_url"]
        else:
            raise Exception("Missing awe_service_url")

        if service_urls.has_key("shock_service_url"):
            self.awe_service_url = service_urls["shock_service_url"]
        else:
            raise Exception("Missing shock_service_url")

        if service_urls.has_key("workspace_service_url"):        
            self.workspace_client = biokbase.workspace.client.Workspace(url=service_urls["workspace_service_url"], token=self.token)
        else:
            raise Exception("Missing workspace_service_url")

        if service_urls.has_key("handle_service_url"):        
            self.handle_client = HandleClient(url=service_urls["handle_service_url"], token=self.token)
        else:
            raise Exception("Missing handle_service_url")
    

class TransformClientDriver(TransformDriver):
    def __init__(self, service_urls=dict(), logger=None):
        super(TransformDriver, self).__init__(service_urls, logger)

    def get_workspace_object_list(self, workspace_name=None, object_name=None):
        object_list = self.workspace_client.list_objects({"workspaces": [workspace_name]})
        return [x for x in object_list if object_name in x[1]]


    def get_workspace_object_contents(self, workspace_name=None, object_name=None):
        return self.workspace_client.get_objects([{"workspace": workspace_name, "name": object_name}])


    def get_job_debug(self, awe_job_id=None, ujs_job_id=None):
        debug_details = dict()
        debug_details["ujs"] = dict()
        debug_details["ujs"]["error"] = self.ujs_client.get_detailed_error(ujs_job_id)
        debug_details["ujs"]["results"] = self.ujs_client.get_results(ujs_job_id)

        header = dict()
        header["Authorization"] = "Oauth {0}".format(self.token)

        debug_details["awe"] = dict()    
        # check awe job output
        awe_details = requests.get("{0}/job/{1}".format(self.awe_service_url,awe_job_id), headers=header, verify=True)
        debug_details["awe"]["details"] = awe_details.json()["data"]
    
        awe_stdout = requests.get("{0}/work/{1}?report=stdout".format(self.awe_service_url,
                                  debug_details["awe"]["details"]["tasks"][0]["taskid"]+"_0"), 
                                  headers=header, verify=True).json()["data"]
        awe_stderr = requests.get("{0}/work/{1}?report=stderr".format(self.awe_service_url,
                                  debug_details["awe"]["details"]["tasks"][0]["taskid"]+"_0"), 
                                  headers=header, verify=True).json()["data"]
        
        debug_details["awe"]["stdout"] = awe_stdout
        debug_details["awe"]["stderr"] = awe_stderr
        
        return debug_details

    
    def get_job_results(self, ujs_job_id=None):
        return self.ujs_client.get_results(ujs_job_id)


    def monitor_job(self, awe_job_id=None, ujs_job_id=None, 
                    success_message="Job completed!",
                    error_message="Job failed!"):
        completed = ["complete", "success"]
        error = ["error", "fail"]

        header = dict()
        header["Authorization"] = "Oauth {0}".format(self.token)
        
        # wait for UJS to complete    
        last_status = ""
        start = datetime.datetime.utcnow()
        while 1:        
            try:
                status = self.ujs_client.get_job_status(ujs_job_id)
            except Exception, e:
                self.logger.error("Issue connecting to UJS!")
                raise
        
            if last_status != status[2]:
                self.logger.info("{0} status update: {1}".format(status[0], status[2]))
                last_status = status[2]
            
            if status[1] in completed:
                self.logger.info("{0}".format(success_message))
                return (True, status)
            elif status[1] in error:
                self.logger.info("{0}".format(error_message))
                return (False, status)

    
class TransformTaskRunnerDriver(TransformDriver):
    def __init__(self, service_urls=dict(), logger=None, plugin_directory=None):
        super(TransformDriver, self).__init__(service_urls, logger)
        
        if plugin_directory is None or not os.path.exists(plugin_directory):
            raise ("No plugins directory found!")
        
        self.load_plugins()

        
    def load_plugins(self):
        self.pluginManager = handler_utils.PluginManager(directory=plugin_directory, logger=self.logger)


    def run_job(self, method=None, arguments=None, description=None):
        if method == "upload":
            command_list = ["trns_upload_taskrunner"]
        elif method == "download":
            command_list = ["trns_download_taskrunner"]
        elif method == "convert":
            command_list = ["trns_convert_taskrunner"]
        else:
            raise Exception("Unrecognized method {0}.  Unable to begin.".format(method))

        if arguments is None:
            raise Exception("Missing arguments")

        arguments["job_details"] = self.pluginManager.get_job_details(method,input_object)

        for k in arguments:
            if type(arguments[x]) == type(dict()):
                args[x] = base64.urlsafe_b64encode(simplejson.dumps(arguments[x]))

            command_list.append("--{0}".format(k))
            command_list.append("{0}".format(arguments[k]))

        estimated_running_time = datetime.datetime.utcnow() + datetime.timedelta(minutes=int(3000))
        ujs_job_id = self.ujs_client.create_and_start_job(self.token, 
                                                          "Starting", 
                                                          description, 
                                                          {"ptype": "task", "max": 100}, 
                                                          estimated_running_time.strftime('%Y-%m-%dT%H:%M:%S+0000'));
        
        taskrunner = subprocess.Popen(command_list, stderr=subprocess.PIPE)
        stdout, stderr = task.communicate()

        task_output = dict()
        task_output["stdout"] = stdout
        task_output["stderr"] = stderr
                
        if task.returncode != 0:
            return (False, task_output)
        else:
            return (True, task_output)



class TransformClientTerminalDriver(TransformClientDriver):
    def __init__(self, service_urls=dict(), logger=biokbase.Transform.script_utils.stdoutlogger(__file__)):
        super(TransformClientDriver, self).__init__(service_urls)

        if service_urls.has_key("fba_service_url"):        
            self.fba_service_url = service_urls["fba_service_url"]
        else:
            self.logger.warning("Missing fba_service_url")
                
        self.terminal = blessings.Terminal()
        

    def show_workspace_object_list(self, workspace_name=None, object_name=None):
        object_list = self.get_workspace_object_list(workspace_name, object_name)
        
        print self.terminal.blue("\tYour KBase data objects:")
        
        for x in sorted(object_list):
            elapsed_time = datetime.datetime.utcnow().replace(tzinfo=dateutil.tz.tzutc()) - dateutil.parser.parse(x[3])
            print "\t\tlast modified: {0}\n\t\tname: {1}\n\t\ttype: {2}\n\t\tsize: {3:d}\n".format(elapsed_time, x[1], x[2], x[-2])


    def show_workspace_object_contents(self, workspace_name=None, object_name=None):
        object_contents = self.get_workspace_object_contents(workspace_name, object_name)
        print object_contents


    def show_job_debug(self, awe_job_id=None, ujs_job_id=None):
        debug_details = self.get_job_debug(awe_job_id, ujs_job_id)
    
        print debug_details
    
        print self.terminal.red("{0}".format(debug_details["ujs"]["error"]))
        print self.terminal.red("{0}".format(debug_details["ujs"]["results"]))

        header = dict()
        header["Authorization"] = "Oauth {0}".format(self.token)
    
        print self.terminal.bold("Additional AWE job details for debugging")
        print self.terminal.red(simplejson.dumps(debug_details["awe"]["details"], sort_keys=True, indent=4))
    
        if debug_details["awe"]["stdout"] is not None:
            stdout_lines = debug_details["awe"]["stdout"].split("\n")
            print self.terminal.red("STDOUT : ")
            for x in stdout_lines:
                print self.terminal.red("\t" + x)
    
        if debug_details["awe"]["stderr"] is not None:
            stderr_lines = debug_details["awe"]["stderr"].split("\n")
            print self.terminal.red("STDERR : ")
            for x in stderr_lines:
                print self.terminal.red("\t" + x)


    def monitor_job(self, awe_job_id=None, ujs_job_id=None, 
                    success_message="Job completed!",
                    error_message="Job failed!"):
        completed = ["complete", "success"]
        error = ["error", "fail"]

        header = dict()
        header["Authorization"] = "Oauth {0}".format(self.token)

        print self.terminal.blue("\tUJS Job Status:")
        
        # wait for UJS to complete    
        last_status = ""
        start = datetime.datetime.utcnow()
        while 1:        
            try:
                status = self.ujs_client.get_job_status(ujs_job_id)
            except Exception, e:
                print self.terminal.red("\t\tIssue connecting to UJS!")
                raise
        
            if last_status != status[2]:
                print "\t\t{0} status update: {1}".format(status[0], status[2])
                last_status = status[2]
            
            if status[1] in completed:
                print self.terminal.green("\t\t{0}\n".format(success_message))
                return (True, status)
            elif status[1] in error:
                print self.terminal.red("\t\t{0}\n".format(error_message))
                return (False, status)


    def download_from_shock(self, shock_service_url=None, shock_id=None, directory=None):
        header = dict()
        header["Authorization"] = "Oauth {0}".format(self.token)

        metadata_response = requests.get("{0}/node/{1}?verbosity=metadata".format(shock_service_url, shock_id), headers=header, stream=True, verify=True)
        shock_metadata = metadata_response.json()['data']
        shockFileName = shock_metadata['file']['name']
        shockFileSize = shock_metadata['file']['size']
        metadata_response.close()
    
        data = requests.get(shock_service_url + '/node/' + shock_id + "?download_raw", headers=header, stream=True)
        size = int(data.headers['content-length'])

        if directory is not None:
            filePath = os.path.join(directory, shockFileName)
        else:
            filePath = shockFileName

        chunkSize = shockFileSize/4
    
        maxChunkSize = 2**30
    
        if chunkSize > maxChunkSize:
            chunkSize = maxChunkSize
    
        term = blessings.Terminal()
        f = open(filePath, 'wb')

        downloaded = 0
        try:
            for chunk in data.iter_content(chunkSize):
                f.write(chunk)
            
                if downloaded + chunkSize > size:
                    downloaded = size
                else:
                    downloaded += chunkSize
        
                print self.terminal.move_up + self.terminal.move_left + "\tDownloaded from shock {0:.2f}%".format(downloaded/float(size) * 100.0)
        except:
            raise        
        finally:
            f.close()
            data.close()
        
        print "\tFile size : {0:f} MB".format(int(os.path.getsize(filePath))/float(1024*1024))

        biokbase.Transform.script_utils.extract_data(self.logger, filePath)


    def post_to_shock(self, shock_service_url=None, filePath=None):
        size = os.path.getsize(filePath)

        term = blessings.Terminal()
    
        print self.terminal.blue("\tShock upload status:\n")
        def progress_indicator(monitor):
            if monitor.bytes_read > size:
                print self.terminal.move_up + self.terminal.move_left + "\t\tPercentage of bytes uploaded to shock 100.00%"                    
            else:
                progress = int(monitor.bytes_read)/float(size) * 100.0
                print self.terminal.move_up + self.terminal.move_left + "\t\tPercentage of bytes uploaded to shock {0:.2f}%".format(progress)                    
            
        #build the header
        header = dict()
        header["Authorization"] = "Oauth {0}".format(self.token)

        dataFile = open(os.path.abspath(filePath))
        encoder = MultipartEncoder(fields={'upload': (os.path.split(filePath)[-1], dataFile)})
        header['Content-Type'] = encoder.content_type
    
        m = MultipartEncoderMonitor(encoder, progress_indicator)

        response = requests.post(shock_service_url + "/node", headers=header, data=m, allow_redirects=True, verify=True)
    
        if not response.ok:
            print response.raise_for_status()

        result = response.json()

        if result['error']:
            raise Exception(result['error'][0])
        else:
            return result["data"]    

