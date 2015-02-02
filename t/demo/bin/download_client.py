#!/usr/bin/env python

import sys
import os
import datetime
import argparse

import blessings
import simplejson

import biokbase.Transform.Client
import biokbase.Transform.script_utils
import biokbase.Transform.drivers


if __name__ == "__main__":
    logger = biokbase.Transform.script_utils.stdoutlogger(__file__)

    parser = argparse.ArgumentParser(description='KBase Download demo and client')
    parser.add_argument('--demo', action="store_true")
    parser.add_argument('--ujs_service_url', nargs='?', help='UserandJobState service for monitoring progress', const="", default="https://kbase.us/services/userandjobstate/")
    parser.add_argument('--workspace_service_url', nargs='?', help='Workspace service for KBase objects', const="", default="https://kbase.us/services/ws/")
    parser.add_argument('--awe_service_url', nargs='?', help='AWE service for additional job monitoring', const="", default="http://140.221.67.3:7080")
    parser.add_argument('--transform_service_url', nargs='?', help='Transform service that handles the data conversion to KBase', const="", default="http://140.221.67.3:7778/")

    parser.add_argument('--external_type', nargs='?', help='the external type of the data', const="", default="")
    parser.add_argument('--kbase_type', nargs='?', help='the kbase object type to create', const="", default="")
    parser.add_argument('--workspace_name', nargs='?', help='name of the workspace where your objects should be created', const="", default="upload_testing")
    parser.add_argument('--object_name', nargs='?', help='name of the workspace object to create', const="", default="")
    parser.add_argument('--download_path', nargs='?', help='path to place downloaded files for validation', const=".", default=".")

    parser.add_argument('--config_file', nargs='?', help='path to config file with parameters', const="", default="")
    parser.add_argument('--create_log', help='create pass/fail log file', action='store_true')

    args = parser.parse_args()

    token = biokbase.Transform.script_utils.get_token()

    inputs = list()
    services = dict()

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
                 "workspace_name": args.workspace_name,
                 "downloadPath": args.download_path
                }
            }

            services = {"shock_service_url": args.shock_service_url,
                        "ujs_service_url": args.ujs_service_url,
                        "workspace_service_url": args.workspace_service_url,
                        "awe_service_url": args.awe_service_url,
                        "transform_service_url": args.transform_service_url,
                        "handle_service_url": args.handle_service_url}

        workspace = args.workspace_name    
    else:
        if "kbasetest" not in token and len(args.workspace.strip()) == 0:
            print "If you are running the demo as a different user than kbasetest, you need to provide the name of your workspace with --workspace."
            sys.exit(0)
        else:
            if args.workspace_name is not None:
                workspace = args.workspace_name
            else :
                workspace = "upload_testing"

        
        f = open("conf/download/download_demo.cfg")
        config = simplejson.loads(f.read())
        f.close()

        services = config["services"]
        inputs = config["download"]

    
    stamp = datetime.datetime.now().isoformat()
    os.mkdir(stamp)

    download_driver = biokbase.Transform.drivers.TransformClientTerminalDriver(services)
    
    term = blessings.Terminal()
    for x in inputs:
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

            input_object = dict()
            input_object["external_type"] = external_type
            input_object["kbase_type"] = kbase_type
            input_object["workspace_name"] = ws_name
            input_object["object_name"] = object_name

            if optional_arguments is not None:
                input_object["optional_arguments"] = optional_arguments
            else:
                input_object["optional_arguments"] = {"transform": {}}

            transform_client = biokbase.Transform.Client.Transform(url=services["transform_service_url"], token=token)            
            awe_job_id, ujs_job_id = transform_client.download(input_object)
            
            print term.blue("\tTransform service download requested:")
            print "\t\tConverting from {0} => {1}\n\t\tUsing workspace {2} with object name {3}".format(kbase_type,external_type,workspace,object_name)
            print term.blue("\tTransform service responded with job ids:")
            print "\t\tAWE job id {0}\n\t\tUJS job id {1}".format(awe_job_id, ujs_job_id)
         
            job_exit_status = download_driver.monitor_job(awe_job_id, ujs_job_id)

            if not job_exit_status[0]:                
                download_driver.show_job_debug(awe_job_id, ujs_job_id)
                raise Exception("KBase Download exited with an error")
            
            results = download_driver.get_job_results(ujs_job_id)
            
            print term.bold("Step 2: Grab data from SHOCK\n")
            download_driver.download_from_shock(results["shockurl"], results["results"][0]["id"], downloadPath)
        
            print term.green("\tShock download of {0} successful.\n\n".format(downloadPath))
        except Exception, e:
            print e.message

