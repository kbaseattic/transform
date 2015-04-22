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
import biokbase.userandjobstate.client
import biokbase.workspace.client



if __name__ == "__main__":
    logger = biokbase.Transform.script_utils.stderrlogger(__file__)

    parser = argparse.ArgumentParser(description='KBase Convert demo and client')
    parser.add_argument('--demo', action="store_true")
    parser.add_argument('--ujs_service_url', nargs='?', help='UserandJobState service for monitoring progress', const="", default="https://kbase.us/services/userandjobstate/")
    parser.add_argument('--workspace_service_url', nargs='?', help='Workspace service for KBase objects', const="", default="https://kbase.us/services/ws/")
    parser.add_argument('--awe_service_url', nargs='?', help='AWE service for additional job monitoring', const="", default="http://140.221.67.242:7080")
    parser.add_argument('--transform_service_url', nargs='?', help='Transform service that handles the data conversion to KBase', const="", default="http://140.221.67.242:7778/")
    parser.add_argument('--handle_service_url', nargs='?', help='Handle service that handles the data conversion to KBase', const="", default="https://kbase.us/services/handle_service/")

    parser.add_argument('--source_kbase_type', nargs='?', help='the source type of the data')
    parser.add_argument('--source_workspace_name', nargs='?', help='name of the source workspace', const="", default="gavinws")
    parser.add_argument('--source_object_name', nargs='?', help='name of the workspace object', const="", default="")

    parser.add_argument('--destination_kbase_type', nargs='?', help='the kbase object type to create')
    parser.add_argument('--destination_workspace_name', nargs='?', help='name of the workspace where your objects should be created', const="", default="upload_testing")
    parser.add_argument('--destination_object_name', nargs='?', help='name of the workspace object to create')

    parser.add_argument('--config_file', nargs='?', help='path to config file with parameters', const="", default="")

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
            inputs = config["convert"]
        else:
            inputs = {"user": 
                {"source_kbase_type": args.source_kbase_type,
                 "source_workspace_name": args.source_workspace_name,
                 "source_object_name": args.source_object_name,
                 "destination_kbase_type": args.destination_kbase_type,
                 "destination_workspace_name": args.destination_workspace_name,
                 "destination_object_name": args.destination_object_name
                }
            }
                
            services = {"shock_service_url": args.shock_service_url,
                        "ujs_service_url": args.ujs_service_url,
                        "workspace_service_url": args.workspace_service_url,
                        "awe_service_url": args.awe_service_url,
                        "transform_service_url": args.transform_service_url,
                        "handle_service_url": args.handle_service_url}
    else:
        if "kbasetest" not in token:
            print "You must be logged in as kbasetoken to run the demo."
        
        f = open("conf/convert/convert_demo.cfg")
        config = simplejson.loads(f.read())
        f.close()

        services = config["services"]
        inputs = config["convert"]
    

    stamp = datetime.datetime.now().isoformat()
    os.mkdir(stamp)
    
    convert_driver = biokbase.Transform.drivers.TransformClientTerminalDriver(services, logger=logger)
    
    term = blessings.Terminal()
    for x in inputs:
        source_kbase_type = inputs[x]["source_kbase_type"]
        source_workspace_name = inputs[x]["source_workspace_name"]
        source_object_name = inputs[x]["source_object_name"]
        destination_kbase_type = inputs[x]["destination_kbase_type"]
        destination_workspace_name = inputs[x]["destination_workspace_name"]
        destination_object_name = inputs[x]["destination_object_name"]

        optional_arguments = None
        if inputs[x].has_key("optional_arguments"):
            optional_arguments = inputs[x]["optional_arguments"]

        print "\n\n"
        print "\t", term.bold_underline_bright_magenta("{0}").format(x.upper())
        print "\t", term.bold("#"*80)
        print "\t", term.bold_white_on_black("Converting {0} => {1}".format(source_kbase_type,destination_kbase_type))
        print "\t", term.bold("#"*80)

        #conversionDownloadPath = os.path.join(stamp, source_kbase_type + "_to_" + destination_kbase_type)
        
        #try:
        #    os.mkdir(conversionDownloadPath)
        #except:
        #    pass
        #
        #downloadPath = os.path.join(conversionDownloadPath)

        try:
            print "\t", term.bold("Step 1: Make KBase type conversion request")
            
            input_object = dict()
            input_object["source_kbase_type"] = source_kbase_type
            input_object["source_workspace_name"] = source_workspace_name
            input_object["source_object_name"] = source_object_name
            input_object["destination_kbase_type"] = destination_kbase_type
            input_object["destination_workspace_name"] = destination_workspace_name
            input_object["destination_object_name"] = destination_object_name

            if optional_arguments is not None:
                input_object["optional_arguments"] = optional_arguments
            else:
                input_object["optional_arguments"] = {"transform": {}}

            transform_client = biokbase.Transform.Client.Transform(url=services["transform_service_url"], token=token)
            awe_job_id, ujs_job_id = transform_client.convert(input_object)
            
            print term.blue("\tTransform service conversion requested:")
            print "\t\tConverting from {0} => {1}".format(source_kbase_type, destination_kbase_type)
            print "\t\tSaving to workspace {0} with object name {1}".format(destination_workspace_name,destination_object_name)

            print term.blue("\tTransform service responded with job ids:")
            print "\t\tAWE job id {0}\n\t\tUJS job id {1}".format(awe_job_id, ujs_job_id)

            job_exit_status = convert_driver.monitor_job(awe_job_id, ujs_job_id)

            if not job_exit_status[0]:                
                convert_driver.show_job_debug(awe_job_id, ujs_job_id)
                raise Exception("KBase Convert exited with an error")

            print term.green("\tConversion successful.  Yaks win.\n\n")
        
            convert_driver.show_workspace_object_list(destination_workspace_name, destination_object_name)
            convert_driver.show_workspace_object_contents(destination_workspace_name, destination_object_name)
        except Exception, e:
            print e.message

