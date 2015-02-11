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

def show_workspace_object_list(workspace_url, workspace_name, object_name, token):
    print term.blue("\tYour KBase data objects:")
    
    c = biokbase.workspace.client.Workspace(workspace_url, token=token)
    object_list = c.list_objects({"workspaces": [workspace_name]})
    
    object_list = [x for x in object_list if object_name in x[1]]

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
    error = ["error", "fail"]
    
    term = blessings.Terminal()

    header = dict()
    header["Authorization"] = "Oauth {0}".format(token)

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
            status[1] = "error"
            status[2] = "Caught Exception"
        
        if (datetime.datetime.utcnow() - start).seconds > time_limit:
            print "\t\tJob is taking longer than it should, check debugging messages for more information."
            status[1] = "error"
            status[2] = "Timeout"            
        
        if last_status != status[2]:
            print "\t\t{0} status update: {1}".format(status[0], status[2])
            last_status = status[2]
        
        if status[1].startswith("http://"):
            print term.green("\t\tKBase download completed!\n")
            return status
            break
        elif status[1] in error:
            print term.red("\t\tOur job failed!\n")
            
            print term.bold("Additional AWE job details for debugging")
            # check awe job output
            awe_details = requests.get("{0}/job/{1}".format(awe_url,awe_id), headers=header, verify=True)
            job_info = awe_details.json()["data"]
            print term.red(json.dumps(job_info, sort_keys=True, indent=4))
            
            awe_stdout = requests.get("{0}/work/{1}?report=stdout".format(awe_url,job_info["tasks"][0]["taskid"]+"_0"), headers=header, verify=True)
            print term.red("STDOUT : " + json.dumps(awe_stdout.json()["data"], sort_keys=True, indent=4))
            
            awe_stderr = requests.get("{0}/work/{1}?report=stderr".format(awe_url,job_info["tasks"][0]["taskid"]+"_0"), headers=header, verify=True)
            print term.red("STDERR : " + json.dumps(awe_stderr.json()["data"], sort_keys=True, indent=4))
            
            break
    

def download(transform_url, options, token):
    c = biokbase.Transform.Client.Transform(url=transform_url, token=token)

    response = c.download(options)        
    return response


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

    parser = argparse.ArgumentParser(description='KBase Download script test driver')
    parser.add_argument('--demo', action="store_true")
    parser.add_argument('--ujs_service_url', nargs='?', help='UserandJobState service for monitoring progress', const="", default="https://kbase.us/services/userandjobstate/")
    parser.add_argument('--workspace_service_url', nargs='?', help='Workspace service for KBase objects', const="", default="https://kbase.us/services/ws/")
    parser.add_argument('--awe_service_url', nargs='?', help='AWE service for additional job monitoring', const="", default="http://140.221.67.3:7080")
    parser.add_argument('--transform_service_url', nargs='?', help='Transform service that handles the data conversion to KBase', const="", default="http://140.221.67.3:7778/")
    parser.add_argument('--handle_service_url', nargs='?', help='Handle service for KBase handle', const="", default="https://kbase.us/services/handle_service")

    parser.add_argument('--external_type', nargs='?', help='the external type of the data', const="", default="")
    parser.add_argument('--kbase_type', nargs='?', help='the kbase object type to create', const="", default="")
    parser.add_argument('--workspace', nargs='?', help='name of the workspace where your objects should be created', const="", default="upload_testing")
    parser.add_argument('--object_name', nargs='?', help='name of the workspace object to create', const="", default="")
    parser.add_argument('--download_path', nargs='?', help='path to place downloaded files for validation', const=".", default=".")
    #parser.add_argument('--handler', help='Client bypass test', dest="handler_mode", action='store_true')
    #parser.add_argument('--client', help='Client mode test', dest="handler_mode", action='store_false')
    #parser.set_defaults(handler_mode=False)
    ## TODO: change the default path to be relative to __FILE__
    parser.add_argument('--config_file', nargs='?', help='path to config file with parameters', const="", default="")
    #parser.add_argument('--verify', help='verify uploaded files', action="store_true")
    parser.add_argument('--plugin_directory', nargs='?', help='path to the plugin dir', const="", default="/kb/dev_container/modules/transform/plugins/configs")

    args = parser.parse_args()

    print args

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
            inputs = config["download"]
        else:
            inputs = {"user": 
                {"external_type": args.external_type,
                 "kbase_type": args.kbase_type,
                 "object_name": args.object_name,
                 "workspace_name" : args.workspace,
                 "downloadPath": args.download_path,
                 "optional_arguments": simplejson.loads(args.optional_arguments)
                }
            }

            services = {"shock_service_url": args.shock_service_url,
                        "ujs_service_url": args.ujs_service_url,
                        "workspace_service_url": args.workspace_service_url,
                        "awe_service_url": args.awe_service_url,
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
                

        f = open("conf/download/download_demo.cfg")
        config = simplejson.loads(f.read())
        f.close()

        services = config["services"]
        inputs = config["download"]
    

    uc = biokbase.userandjobstate.client.UserAndJobState(url=args.ujs_service_url, token=token)
    
    stamp = datetime.datetime.now().isoformat()
    os.mkdir(stamp)
    
    download_driver = biokbase.Transform.drivers.TransformClientTerminalDriver(service_urls=services)
    plugins = biokbase.Transform.handler_utils.PlugIns(args.plugin_directory)

    term = blessings.Terminal()
    for x in sorted(inputs):
        external_type = inputs[x]["external_type"]
        kbase_type = inputs[x]["kbase_type"]
        object_name = inputs[x]["object_name"]

        if inputs[x].has_key("workspace_name") and inputs[x]["workspace_name"]:
            ws_name = inputs[x]["workspace_name"]
        else:
            ws_name = workspace

        optional_arguments = None
        if inputs[x].has_key("optional_arguments"):
            optional_arguments = inputs[x]["optional_arguments"]

        print "\n\n"
        print term.bold("#"*80)
        print term.white_on_black("Converting {0} => {1}".format(kbase_type,external_type))
        print term.bold("#"*80)

        conversionDownloadPath = os.path.join(stamp, kbase_type + "_to_" + external_type)
        try:
            os.mkdir(conversionDownloadPath)
        except:
            pass
        
        downloadPath = os.path.join(conversionDownloadPath)

        try:
            print term.bold("Step 1: Make KBase download request")

            status = 'Initializing'
            description = 'Mock handler testing' #method_hash["ujs_description"]
            #progress = { 'ptype' : method_hash["ujs_ptype"], 'max' : method_hash["ujs_mstep"] };
            progress = { 'ptype' : 'task', 'max' : 100 };
            est = datetime.datetime.utcnow() + datetime.timedelta(minutes=int(3000))
            ujs_job_id = uc.create_and_start_job(token, status, description, progress, est.strftime('%Y-%m-%dT%H:%M:%S+0000'));

            input_object = dict()
            input_object["external_type"] = external_type
            input_object["kbase_type"] = kbase_type
            input_object["job_details"] = plugins.get_job_details('download', input_object)
            input_object["workspace_name"] = ws_name
            input_object["object_name"] = object_name
            input_object["working_directory"] = stamp
            input_object.update(services)
            if input_object.has_key("awe_service_url"): del input_object["awe_service_url"] 
            if input_object.has_key("transform_service_url"): del input_object["transform_service_url"] 

            if optional_arguments is not None:
                input_object["optional_arguments"] = optional_arguments
            else:
                input_object["optional_arguments"] = {"transform": {}}

            for x in input_object:
                if type(input_object[x]) == type(dict()):
                    input_object[x] = base64.urlsafe_b64encode(simplejson.dumps(input_object[x]))


            print term.blue("\tTransform handler download started:")
            command_list = ["trns_download_taskrunner", "--ujs_job_id", ujs_job_id]

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

            results = download_driver.get_job_results(ujs_job_id)

            print results

            print term.bold("Step 2: Grab data from SHOCK\n")
            download_driver.download_from_shock(results["shockurl"], results["results"][0]["id"], downloadPath)
            #download_from_shock(services["shock"], shock_response, downloadPath, token)
            print term.green("\tShock download of {0} successful.\n\n".format(downloadPath))
        except Exception, e:
            print e.message

