#!/usr/bin/env python

import sys
import time
import datetime
import os
import os.path
import io
import json
import pprint

# patch for handling unverified certificates
import ssl
if hasattr(ssl, '_create_unverified_context'):
    ssl._create_default_https_context = ssl._create_unverified_context

# make sure the 3rd party and kbase modules are in the path for importing
sys.path.insert(0,os.path.abspath("venv/lib/python2.7/site-packages/"))

from requests_toolbelt import MultipartEncoder, MultipartEncoderMonitor
import requests
import magic
import blessings
import dateutil.parser
import dateutil.tz

import biokbase.Transform.Client
import biokbase.Transform.script_utils
import biokbase.userandjobstate.client
import biokbase.workspace.client

logger = biokbase.Transform.script_utils.stderrlogger(__file__)


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
            print term.green("\t\tKBase conversion completed!\n")
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
    

def convert(transform_url, options, token):
    c = biokbase.Transform.Client.Transform(url=transform_url, token=token)

    response = c.convert(options)        
    return response



if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='KBase Upload demo and client')
    parser.add_argument('--demo', action="store_true")
    parser.add_argument('--ujs_service_url', nargs='?', help='UserandJobState service for monitoring progress', const="", default="https://kbase.us/services/userandjobstate/")
    parser.add_argument('--workspace_service_url', nargs='?', help='Workspace service for KBase objects', const="", default="https://kbase.us/services/ws/")
    parser.add_argument('--awe_service_url', nargs='?', help='AWE service for additional job monitoring', const="", default="http://140.221.67.242:7080")
    parser.add_argument('--transform_service_url', nargs='?', help='Transform service that handles the data conversion to KBase', const="", default="http://140.221.67.242:7778/")

    parser.add_argument('--source_kbase_type', nargs='?', help='the source type of the data')
    parser.add_argument('--source_workspace_name', nargs='?', help='name of the source workspace', const="", default="gavinws")
    parser.add_argument('--source_object_name', nargs='?', help='name of the workspace object', const="", default="")

    parser.add_argument('--destination_kbase_type', nargs='?', help='the kbase object type to create')
    parser.add_argument('--destination_workspace_name', nargs='?', help='name of the workspace where your objects should be created', const="", default="upload_testing")
    parser.add_argument('--destination_object_name', nargs='?', help='name of the workspace object to create')

    args = parser.parse_args()

    token = os.environ.get("KB_AUTH_TOKEN")
    if token is None:
        if os.path.exists(os.path.expanduser("~/.kbase_config")):
            f = open(os.path.expanduser("~/.kbase_config", 'r'))
            config = f.read()
            if "token=" in config:
                token = config.split("token=")[1].split("\n",1)[0]            
            else:
                raise Exception("Unable to find KBase token!")
        else:
            raise Exception("Unable to find KBase token!")

    if not args.demo:
        user_inputs = {"source_kbase_type": args.source_kbase_type,
                       "source_workspace_name": args.source_workspace_name,
                       "source_object_name": args.source_object_name,
                       "destination_kbase_type": args.destination_kbase_type,
                       "destination_workspace_name": args.destination_workspace_name,
                       "destination_object_name": args.destination_object_name}

        demos = [user_inputs]
    else:
        bigyakattack = {"source_kbase_type": "KBaseFile.AssemblyFile",
                        "source_workspace_name": "gavinws",
                        "source_object_name": "final.assembly.fasta",
                        "destination_kbase_type": "KBaseGenomes.ContigSet",
                        "destination_workspace_name": "upload_testing",
                        "destination_object_name": "tastythunderyak"}

        demos = [bigyakattack]
    

    services = {"ujs": args.ujs_service_url,
                "workspace": args.workspace_service_url,
                "awe": args.awe_service_url,
                "transform": args.transform_service_url}

    
    stamp = datetime.datetime.now().isoformat()
    os.mkdir(stamp)
    
    term = blessings.Terminal()
    for demo_inputs in demos:
        source_kbase_type = demo_inputs["source_kbase_type"]
        source_workspace_name = demo_inputs["source_workspace_name"]
        source_object_name = demo_inputs["source_object_name"]
        destination_kbase_type = demo_inputs["destination_kbase_type"]
        destination_workspace_name = demo_inputs["destination_workspace_name"]
        destination_object_name = demo_inputs["destination_object_name"]

        print "\n\n"
        print term.bold("#"*80)
        print term.white_on_black("Converting {0} => {1}".format(source_kbase_type,destination_kbase_type))
        print term.bold("#"*80)

        conversionDownloadPath = os.path.join(stamp, source_kbase_type + "_to_" + destination_kbase_type)
        
        try:
            os.mkdir(conversionDownloadPath)
        except:
            pass
        
        downloadPath = os.path.join(conversionDownloadPath)

        try:
            print term.bold("Step 1: Make KBase type conversion request")
            convert_response = convert(services["transform"], 
                                       {"source_kbase_type": source_kbase_type,
                                        "source_workspace_name": source_workspace_name,
                                        "source_object_name": source_object_name,
                                        "destination_kbase_type": destination_kbase_type,
                                        "destination_workspace_name": destination_workspace_name,
                                        "destination_object_name": destination_object_name
                                       }, 
                                       token)
            print term.blue("\tTransform service conversion requested:")
            print "\t\tConverting from {0} => {1}".format(source_kbase_type, destination_kbase_type)
            print "\t\tSaving to workspace {0} with object name {1}".format(destination_workspace_name,destination_object_name)

            print term.blue("\tTransform service responded with job ids:")
            print "\t\tAWE job id {0}\n\t\tUJS job id {1}".format(convert_response[0], convert_response[1])

            show_job_progress(services["ujs"], services["awe"], convert_response[0], convert_response[1], token)

            print term.green("\tConversion successful.  Yaks win.\n\n")
        except Exception, e:
            print e.message
            raise

