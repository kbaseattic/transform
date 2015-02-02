#!/usr/bin/env python

import sys
import os
import datetime
import logging
import argparse

import blessings
import simplejson

import biokbase.Transform.Client
import biokbase.Transform.script_utils
import biokbase.Transform.drivers


if __name__ == "__main__":
    logger = biokbase.Transform.script_utils.stdoutlogger(__file__)

    parser = argparse.ArgumentParser(description='KBase Upload client driver')
    parser.add_argument('--demo', action="store_true")
    parser.add_argument('--shock_service_url', nargs='?', help='SHOCK service to upload local files', const="", default="https://kbase.us/services/shock-api/")
    parser.add_argument('--ujs_service_url', nargs='?', help='UserandJobState service for monitoring progress', const="", default="https://kbase.us/services/userandjobstate/")
    parser.add_argument('--workspace_service_url', nargs='?', help='Workspace service for KBase objects', const="", default="https://kbase.us/services/ws/")
    parser.add_argument('--awe_service_url', nargs='?', help='AWE service for additional job monitoring', const="", default="http://140.221.67.242:7080")
    parser.add_argument('--transform_service_url', nargs='?', help='Transform service that handles the data conversion to KBase', const="", default="http://140.221.67.242:7778/")
    parser.add_argument('--handle_service_url', nargs='?', help='Handle service for KBase handle', const="", default="https://kbase.us/services/handle_service")

    parser.add_argument('--external_type', nargs='?', help='the external type of the data', const="", default="")
    parser.add_argument('--kbase_type', nargs='?', help='the kbase object type to create', const="", default="")
    parser.add_argument('--workspace_name', nargs='?', help='name of the workspace where your objects should be created', const="", default="upload_testing")
    parser.add_argument('--object_name', nargs='?', help='name of the workspace object to create', const="", default="")
    parser.add_argument('--url_mapping', nargs='?', help='dictionary of urls to process', action='store', default="{}")
    parser.add_argument('--optional_arguments', nargs='?', help='optional and/or custom arguments for the service call', action='store', default="{}")
    
    parser.add_argument('--file_path', nargs='?', help='path to file for upload', const="", default="")
    parser.add_argument('--download_path', nargs='?', help='path to place downloaded files for validation', const=".", default=".")
    parser.add_argument('--config_file', nargs='?', help='path to config file with parameters', const="", default="")
    parser.add_argument('--verify', help='verify uploaded files', action="store_true")
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
            inputs = config["upload"]
        else:
            inputs = {"user": 
                {"external_type": args.external_type,
                 "kbase_type": args.kbase_type,
                 "object_name": args.object_name,
                 "filePath": args.file_path,
                 "downloadPath": args.download_path,
                 "url_mapping" : simplejson.loads(args.url_mapping)
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

        
        f = open("conf/upload_demo.cfg")
        config = simplejson.loads(f.read())
        f.close()

        services = config["services"]
        inputs = config["upload"]

    
    stamp = datetime.datetime.now().isoformat()
    os.mkdir(stamp)
    
    if args.create_log:
        status_logger = logging.getLogger("status")
        file_handler = logging.FileHandler(os.path.join(stamp,'pass_fail.log'))
        status_logger.addHandler(file_handler)
        status_logger.setLevel(logging.INFO)
        status_logger.info("KBase Upload testing began at {0}".format(datetime.datetime.utcnow().isoformat()))
    
    upload_driver = biokbase.Transform.drivers.TransformClientTerminalDriver(services)
    
    term = blessings.Terminal()
    for x in sorted(inputs):
        external_type = inputs[x]["external_type"]
        kbase_type = inputs[x]["kbase_type"]
        object_name = inputs[x]["object_name"]

        optional_arguments = None
        if inputs[x].has_key("optional_arguments"):
            optional_arguments = inputs[x]["optional_arguments"]

        passed = True

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

                    shock_response = upload_driver.post_to_shock(services["shock_service_url"], filePath)
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
                        upload_driver.download_from_shock(services["shock_service_url"], shock_response["id"], downloadFilePath)
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
            
            input_object = dict()
            input_object["external_type"] = external_type
            input_object["kbase_type"] = kbase_type
            input_object["workspace_name"] = workspace
            input_object["object_name"] = object_name
            input_object["url_mapping"] = inputs[x]["url_mapping"]

            if optional_arguments is not None:
                input_object["optional_arguments"] = optional_arguments
            else:
                input_object["optional_arguments"] = {'validate': {}, 'transform': {}}

            transform_client = biokbase.Transform.Client.Transform(url=services["transform_service_url"], token=token)

            awe_job_id, ujs_job_id = transform_client.upload(input_object)
 
            print term.blue("\tTransform service upload requested:")
            print "\t\tConverting from {0} => {1}\n\t\tUsing workspace {2} with object name {3}".format(external_type,kbase_type,workspace,object_name)
            print term.blue("\tTransform service responded with job ids:")
            print "\t\tAWE job id {0}\n\t\tUJS job id {1}".format(awe_job_id, ujs_job_id)
            upload_step += 1
 
            job_exit_status = upload_driver.monitor_job(awe_job_id, ujs_job_id)
            
            print job_exit_status
            
            if not job_exit_status[0]:
                print upload_driver.get_job_debug(awe_job_id, ujs_job_id)                
                upload_driver.show_job_debug(awe_job_id, ujs_job_id)
                raise Exception("KBase Upload exited with an error")

            print term.bold("Step {0}: View or use workspace objects".format(upload_step))
            upload_driver.show_workspace_object_list(workspace, object_name)
        except Exception, e:
            passed = False
            print e.message
            print e

        if args.create_log:
            if passed:
                passed_message = "PASSED"
            else:
                passed_message = "FAILED"
            
            status_logger.info("{0} : Converting {1} => {2} {3}".format(x,external_type,kbase_type,passed_message))

