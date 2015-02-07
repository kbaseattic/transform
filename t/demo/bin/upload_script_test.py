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
import pprint
import subprocess
import base64

# patch for handling unverified certificates
import ssl
if hasattr(ssl, '_create_unverified_context'):
    ssl._create_default_https_context = ssl._create_unverified_context

# make sure the 3rd party and kbase modules are in the path for importing
#sys.path.insert(0,os.path.abspath("venv/lib/python2.7/site-packages/"))

from requests_toolbelt import MultipartEncoder, MultipartEncoderMonitor
import requests
import magic
import blessings
import dateutil.parser
import dateutil.tz
import simplejson

import biokbase.Transform.Client
import biokbase.Transform.script_utils as script_utils
import biokbase.Transform.handler_utils
import biokbase.Transform.drivers
import biokbase.userandjobstate.client
import biokbase.workspace.client

logger = biokbase.Transform.script_utils.stdoutlogger(__file__)

configs = dict()

def read_configs(configs_directory):
    for x in os.listdir(configs_directory):
        with open(os.path.join(configs_directory,x), 'r') as f:
            c = simplejson.loads(f.read())
            configs[c["script_type"]] = c
    

def validate_files(input_directory, external_type):
    if external_type in configs["validate"]:
        print "validate"


def show_workspace_object_list(workspace_url, workspace_name, object_name, token):
    print term.blue("\tYour KBase data objects:")
    
    c = biokbase.workspace.client.Workspace(workspace_url, token=token)
    object_list = c.list_objects({"workspaces": [workspace_name]})
    
    object_list = [x for x in object_list if object_name == x[1]]

    for x in sorted(object_list):
        elapsed_time = datetime.datetime.utcnow().replace(tzinfo=dateutil.tz.tzutc()) - dateutil.parser.parse(x[3])
        print "\t\thow_recent: {0}\n\t\tname: {1}\n\t\ttype: {2}\n\t\tsize: {3:d}\n".format(elapsed_time, x[1], x[2], x[-2])


def show_workspace_object_contents(workspace_url, workspace_name, object_name, token):
    c = biokbase.workspace.client.Workspace(workspace_url, token=token)
    object_contents = c.get_objects([{"workspace": workspace_name, "objid": 2}])
    print object_contents


def show_job_progress(ujs_url, awe_url, awe_id, ujs_id, token):
    c = biokbase.userandjobstate.client.UserAndJobState(url=ujs_url, token=token)

    completed = ["complete", "success"]
    error = ["error", "fail", "ERROR"]
    
    term = blessings.Terminal()

    header = dict()
    header["Authorization"] = "Oauth %s" % token

    print term.blue("\tUJS Job Status:")
    # wait for UJS to complete    
    last_status = ""
    time_limit = 40
    start = datetime.datetime.utcnow()
    while 1:        
        try:
            status = c.get_job_status(ujs_id)
        except Exception, e:
            print term.red("\t\tIssue connecting to UJS!")
            status[1] = "ERROR"
            status[2] = "Caught Exception"
        
        if (datetime.datetime.utcnow() - start).seconds > time_limit:
            print "\t\tJob is taking longer than it should, check debugging messages for more information."
            status[1] = "ERROR"
            status[2] = "Timeout"            
        
        if last_status != status[2]:
            print "\t\t{0} status update: {1}".format(status[0], status[2])
            last_status = status[2]
        
        if status[1] in completed:
            print term.green("\t\tKBase upload completed!\n")
            break
        elif status[1] in error:
            print term.red("\t\tOur job failed!\n")
            
            print term.red("{0}".format(c.get_detailed_error(ujs_id)))
            print term.red("{0}".format(c.get_results(ujs_id)))
            
            print term.bold("Additional AWE job details for debugging")
            # check awe job output
            awe_details = requests.get("{0}/job/{1}".format(awe_url,awe_id), headers=header, verify=True)
            job_info = awe_details.json()["data"]
            print term.red(simplejson.dumps(job_info, sort_keys=True, indent=4))
            
            awe_stdout = requests.get("{0}/work/{1}?report=stdout".format(awe_url,job_info["tasks"][0]["taskid"]+"_0"), headers=header, verify=True)
            print term.red("STDOUT : " + simplejson.dumps(awe_stdout.json()["data"], sort_keys=True, indent=4))
            
            awe_stderr = requests.get("{0}/work/{1}?report=stderr".format(awe_url,job_info["tasks"][0]["taskid"]+"_0"), headers=header, verify=True)
            print term.red("STDERR : " + simplejson.dumps(awe_stderr.json()["data"], sort_keys=True, indent=4))
            
            break
    

def upload(transform_url, options, token):
    c = biokbase.Transform.Client.Transform(url=transform_url, token=token)
    response = c.upload(options)        
    return response



def post_to_shock(shockURL, filePath, token):
    size = os.path.getsize(filePath)

    term = blessings.Terminal()
    
    print term.blue("\tShock upload status:\n")
    def progress_indicator(monitor):
        if monitor.bytes_read > size:
            pass            
        else:
            progress = int(monitor.bytes_read)/float(size) * 100.0
            print term.move_up + term.move_left + "\t\tPercentage of bytes uploaded to shock {0:.2f}%".format(progress)                    
            
    #build the header
    header = dict()
    header["Authorization"] = "Oauth %s" % token

    dataFile = open(os.path.abspath(filePath))
    encoder = MultipartEncoder(fields={'upload': (os.path.split(filePath)[-1], dataFile)})
    header['Content-Type'] = encoder.content_type
    
    m = MultipartEncoderMonitor(encoder, progress_indicator)

    response = requests.post(shockURL + "/node", headers=header, data=m, allow_redirects=True, verify=True)
    
    if not response.ok:
        print response.raise_for_status()

    result = response.json()

    if result['error']:
        raise Exception(result['error'][0])
    else:
        return result["data"]    


def download_from_shock(shockURL, shock_id, filePath, token):
    header = dict()
    header["Authorization"] = "Oauth %s" % token
    
    data = requests.get(shockURL + '/node/' + shock_id + "?download_raw", headers=header, stream=True)
    size = int(data.headers['content-length'])
    
    chunkSize = 10 * 2**20
    download_iter = data.iter_content(chunkSize)

    term = blessings.Terminal()
    f = open(filePath, 'wb')

    downloaded = 0
    try:
        for chunk in download_iter:
            f.write(chunk)
            
            if downloaded + chunkSize > size:
                downloaded = size
            else:
                downloaded += chunkSize
        
            print term.move_up + term.move_left + "\tDownloaded from shock {0:.2f}%".format(downloaded/float(size) * 100.0)
    except:
        raise        
    finally:
        f.close()
        data.close()
        
    print "\tFile size : {0:f} MB".format(int(os.path.getsize(filePath))/float(1024*1024))

    biokbase.Transform.script_utils.extract_data(logger, filePath)



if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='KBase Upload handler test driver')

    parser.add_argument('--demo', action="store_true")
    parser.add_argument('--shock_service_url', nargs='?', help='SHOCK service to upload local files', const="", default="https://kbase.us/services/shock-api/")
    parser.add_argument('--ujs_service_url', nargs='?', help='UserandJobState service for monitoring progress', const="", default="https://kbase.us/services/userandjobstate/")
    parser.add_argument('--workspace_service_url', nargs='?', help='Workspace service for KBase objects', const="", default="https://kbase.us/services/ws/")
    parser.add_argument('--awe_service_url', nargs='?', help='AWE service for additional job monitoring', const="", default="http://140.221.67.242:7080")
    parser.add_argument('--transform_service_url', nargs='?', help='Transform service that handles the data conversion to KBase', const="", default="http://140.221.67.242:7778/")
    parser.add_argument('--handle_service_url', nargs='?', help='Handle service for KBase handle', const="", default="https://kbase.us/services/handle_service")
    parser.add_argument('--fba_service_url', nargs='?', help='FBA service for Model data', const="", default="https://kbase.us/services/handle_service")

    parser.add_argument('--external_type', nargs='?', help='the external type of the data', const="", default="")
    parser.add_argument('--kbase_type', nargs='?', help='the kbase object type to create', const="", default="")
    parser.add_argument('--workspace', nargs='?', help='name of the workspace where your objects should be created', const="", default="upload_testing")
    parser.add_argument('--object_name', nargs='?', help='name of the workspace object to create', const="", default="")
    parser.add_argument('--url_mapping', nargs='?', help='input url mapping', const="", default="{}")
    parser.add_argument('--optional_arguments', nargs='?', help='optional arguments', const="", default='{"validate" : {}, "transform" : {}}')
    parser.add_argument('--plugin_directory', nargs='?', help='path to the plugins directory', const="", default="/kb/dev_container/modules/transform/plugins/configs")

    parser.add_argument('--file_path', nargs='?', help='path to file for upload', const="", default="")
    parser.add_argument('--download_path', nargs='?', help='path to place downloaded files for validation', const=".", default=".")
    parser.add_argument('--config_file', nargs='?', help='path to config file with parameters', const="", default="")
    parser.add_argument('--verify', help='verify uploaded files', action="store_true")
    #parser.add_argument('--create_log', help='create pass/fail log file', action='store_true')

    args = parser.parse_args()

    token = script_utils.get_token()

    plugin = None
    plugin = biokbase.Transform.handler_utils.PlugIns(args.plugin_directory, logger)

    inputs = list()
    if not args.demo:
        if args.config_file:
            f = open(args.config_file, 'r')
            config = simplejson.loads(f.read())
            f.close()
        
            services = config["services"]
            inputs = config["upload"]
        else:
            inputs = {"user": 
                {"external_type": args.external_type,
                 "kbase_type": args.kbase_type,
                 "object_name": args.object_name,
                 "workspace_name" : args.workspace,
                 "filePath": args.file_path,
                 "downloadPath": args.download_path,
                 "optional_arguments": simplejson.loads(args.optional_arguments),
                 "url_mapping" : simplejson.loads(args.url_mapping)
                }
            }

            services = {"shock_service_url": args.shock_service_url,
                        "ujs_service_url": args.ujs_service_url,
                        "workspace_service_url": args.workspace_service_url,
                        "awe_service_url": args.awe_service_url,
                        "fba_service_url": args.awe_service_url,
                        "transform_service_url": args.transform_service_url,
                        "handle_service_url": args.handle_service_url}

        workspace = args.workspace    
    else:
        if "kbasetest" not in token and len(args.workspace.strip()) == 0:
            print "If you are running the demo as a different user than kbasetest, you need to provide the name of your workspace with --workspace."
            sys.exit(0)
        else:
            if args.workspace is not None:
                workspace = args.workspace
            else :
                workspace = "upload_testing"

        
        f = open("conf/upload_demo.cfg")
        config = simplejson.loads(f.read())
        f.close()

        services = config["services"]
        inputs = config["upload"]

    uc = biokbase.userandjobstate.client.UserAndJobState(url=args.ujs_service_url, token=token)



    
    stamp = datetime.datetime.now().isoformat()
    os.mkdir(stamp)
    
    #task_driver = biokbase.Transform.drivers.TransformTaskRunnerDriver(services, args.plugin_directory)
    task_driver = biokbase.Transform.drivers.TransformClientTerminalDriver(services)
    plugins = biokbase.Transform.handler_utils.PlugIns(args.plugin_directory)
    
    term = blessings.Terminal()
    for x in sorted(inputs):
        external_type = inputs[x]["external_type"]
        kbase_type = inputs[x]["kbase_type"]
        object_name = inputs[x]["object_name"]

        optional_arguments = None
        if inputs[x].has_key("optional_arguments"):
            optional_arguments = inputs[x]["optional_arguments"]
        
        print "\n\n"
        print term.bold("#"*80)
        print term.white_on_black("Converting {0} => {1}".format(external_type,kbase_type))
        print term.bold("#"*80)

        files_to_upload = [k for k in inputs[x]["url_mapping"] if inputs[x]["url_mapping"][k].startswith("file://")]

        SIZE_MB = float(1024*1024)

        upload_step = 1
        # check to see if we need to put any files in shock
        if len(files_to_upload) > 0:
            print term.bright_blue("Uploading local files")
            print term.bold("Step {0:d}: Place local files in SHOCK".format(upload_step))
            upload_step += 1

            try: 
                for n in files_to_upload:
                    filePath = inputs[x]["url_mapping"][n].split("file://")[1]
                    fileName = os.path.split(filePath)[-1]
                    print term.blue("\tPreparing to upload {0}".format(filePath))
                    print "\tFile size : {0:f} MB".format(int(os.path.getsize(filePath))/SIZE_MB)

                    shock_response = task_driver.post_to_shock(services["shock_service_url"], filePath)
                    print term.green("\tShock upload of {0} successful.".format(filePath))
                    print "\tShock id : {0}\n\n".format(shock_response['id'])
    
                    inputs[x]["url_mapping"][n] = "{0}/node/{1}".format(services["shock_service_url"],shock_response["id"])
            
                    if args.verify:
                        downloadPath = os.path.join(stamp, external_type + "_to_" + kbase_type)
        
                        try:
                            os.mkdir(downloadPath)
                        except:
                            pass
                        
                        downloadFilePath = os.path.join(downloadPath, fileName)
                        print term.bold("Optional Step: Verify files uploaded to SHOCK\n")
                        task_driver.download_from_shock(services["shock_service_url"], shock_response["id"], downloadFilePath)
                        print term.green("\tShock download of {0} successful.\n\n".format(downloadFilePath))
            except Exception, e:
                passed = False
                print e.message
                raise

        try:
            print term.bright_blue("Uploading from remote http or ftp urls")
            print term.bold("Step {0}: Make KBase upload request with urls of data".format(upload_step))
            print term.bold("Using data from : {0}".format(inputs[x]["url_mapping"].values()))
            upload_step += 1
            
            status = 'Initializing'
            description = 'Mock handler testing' #method_hash["ujs_description"]
            #progress = { 'ptype' : method_hash["ujs_ptype"], 'max' : method_hash["ujs_mstep"] };
            progress = { 'ptype' : 'task', 'max' : 100 };
            est = datetime.datetime.utcnow() + datetime.timedelta(minutes=int(3000))
            ujs_job_id = uc.create_and_start_job(token, status, description, progress, est.strftime('%Y-%m-%dT%H:%M:%S+0000'));
            input_object = dict()
            input_object["external_type"] = external_type
            input_object["kbase_type"] = kbase_type
            input_object["job_details"] = plugins.get_job_details('upload', input_object)
            input_object["workspace_name"] = workspace
            input_object["object_name"] = object_name
            input_object["url_mapping"] = inputs[x]["url_mapping"]
            input_object["working_directory"] = stamp
            input_object.update(services)
            if input_object.has_key("awe_service_url"): del input_object["awe_service_url"] 
            if input_object.has_key("transform_service_url"): del input_object["transform_service_url"] 
            #if input_object.has_key("handle_service_url"): del input_object["handle_service_url"] 

            print term.blue("\tTransform handler upload started:")
            
            if optional_arguments is not None:
                input_object["optional_arguments"] = optional_arguments
            else:
                input_object["optional_arguments"] = {'validate': {}, 'transform': {}}

            for x in input_object:
                if type(input_object[x]) == type(dict()):
                    input_object[x] = base64.urlsafe_b64encode(simplejson.dumps(input_object[x]))

            command_list = ["trns_upload_taskrunner", "--ujs_job_id", ujs_job_id]
            
            for k in input_object:
               command_list.append("--{0}".format(k))
               command_list.append("{0}".format(input_object[k]))

            print "\n\nHandler invocation {0}".format(" ".join(command_list))

            task = subprocess.Popen(command_list, stderr=subprocess.PIPE)
            sub_stdout, sub_stderr = task.communicate()
            
            if sub_stdout is not None:
                print sub_stdout
            if sub_stderr is not None:
                print >> sys.stderr, sub_stderr
            
            if task.returncode != 0:
                raise Exception(sub_stderr)

            print term.bold("Step 3: View or use workspace objects : {0}/{1}".format(workspace, object_name))
            #show_workspace_object_list(services["workspace"], workspace, object_name, token)
            task_driver.show_workspace_object_list(workspace, object_name)
            print term.bold("Step 4: DONE")

            #job_exit_status = task_driver.run_job("upload", input_object, "{0} => {1}".format(external_type,kbase_type))
            #if not job_exit_status[0]:                
            #    print job_exit_status[1]
            #    raise# Exception("KBase Upload exited with an error")

            #print term.bold("Step {0}: View or use workspace objects".format(upload_step))
            #task_driver.show_workspace_object_list(workspace, object_name)

        except Exception, e:
            print e.message
            print e
