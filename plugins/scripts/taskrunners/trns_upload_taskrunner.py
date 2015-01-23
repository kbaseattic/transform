#!/usr/bin/env python

import sys
import os
import datetime
import logging
import argparse
import base64

import simplejson

from biokbase.workspace.client import Workspace
from biokbase.userandjobstate.client import UserAndJobState
from biokbase.Transform import handler_utils
from biokbase.Transform import script_utils

# clean out arguments passed to transform script
remove_keys = ["handler_options","user_options","user_option_groups",
               "url_mapping","developer_description","user_description", 
               "kbase_type", "external_type", "script_type"]

def main():
    """
    KBase Upload task manager for converting from external data formats to KBase objects.
    
    Step 1 - Download the input data and unpack to local files
    Step 2 - Validate the input files
    Step 3 - Transform the input files to KBase Object JSON and save any references
    Step 4 - Save Workspace objects from the JSON and reference info

    Steps 2,3,4 may be combined by certain data transformations, in which case
    only step 3 is executed, with the understanding that it has accepted
    responsibility for validation of the inputs and saving the workspace data.
    
    Args:
        workspace_service_url: URL for a KBase Workspace service where KBase objects 
                               are stored.
        ujs_service_url: URL for a User and Job State service to report task progress
                         back to the user.
        shock_service_url: URL for a KBase SHOCK data store service for storing files 
                           and large reference data.
        handle_service_url: URL for a KBase Handle service that maps permissions from 
                            the Workspace to SHOCK for KBase types that specify a Handle 
                            reference instead of a SHOCK reference.
        url_mapping: A JSON mapping of names to urls that identifies specific data elements
                     as well as special information such as KBase metadata and provenance.
        workspace_name: The name of the destination workspace.
        object_name: The destination object name.
        object_id: A destination object id, which can be used instead of object_name.
        external_type: The external data format being transformed to a KBase type.
                       E.g., FASTA.DNA.Assembly
                       This is simply a string, but denotes the format of the data and
                       some context about what it actually is, which is used to 
                       differentiate between files of the same general format with
                       different fundamental values.                       
        kbase_type: The KBase Workspace type string that indicates the modules and type
                    of the object being created.
        optional_arguments: This is a JSON string containing optional parameters that can
                            be passed in for validation or transformation steps to
                            customize behavior based on available exposed options.
        ujs_job_id: The job id from the User and Job State service that can be used to
                    report status on task progress back to the user.
        job_details: This is a JSON string that passes in the script specific command
                     line options for a given transformation type.  The service pulls
                     these config settings from a script config created by the developer
                     of the transformation script and passes that into the AWE job that
                     calls this script.
        working_directory: The working directory on disk where files can be created and
                           will be cleaned when the job ends with success or failure.
        keep_working_directory: A flag to tell the script not to delete the working
                                directory, which is mainly for debugging purposes.
        debug: Run the taskrunner in debug mode for local execution in a virtualenv.
    
    Returns:
        Literal return value is 0 for success and 1 for failure.
        
        Actual data output is one or more Workspace objects saved to a user's workspace 
        based on input files provided by urls.
        
    Authors:
        Shinjae Yoo, Matt Henderson            
    """

    logger = script_utils.stderrlogger(__file__)
    logger.info("Executing KBase Upload tasks")
    
    script_details = script_utils.parse_docs(main.__doc__)
        
    parser = argparse.ArgumentParser(description=script_details["Description"],
                                     epilog=script_details["Authors"])
    # provided by service config
    parser.add_argument('--workspace_service_url', 
                        help=script_details["Args"]["workspace_service_url"], 
                        action='store', 
                        required=True)
    parser.add_argument('--ujs_service_url', 
                        help=script_details["Args"]["ujs_service_url"], 
                        action='store', 
                        required=True)
    
    # optional because not all KBase Workspace types contain a SHOCK or Handle reference
    parser.add_argument('--shock_service_url', 
                        help=script_details["Args"]["shock_service_url"], 
                        action='store', 
                        default=None)
    parser.add_argument('--handle_service_url', 
                        help=script_details["Args"]["handle_service_url"], 
                        action='store', 
                        default=None)

    # service method inputs
    # data inputs
    parser.add_argument('--url_mapping', 
                        help=script_details["Args"]["url_mapping"], 
                        action='store', 
                        required=True)

    # workspace info for saving the data
    parser.add_argument('--workspace_name', 
                        help=script_details["Args"]["workspace_name"], 
                        action='store', 
                        required=True)
    parser.add_argument('--object_name', 
                        help=script_details["Args"]["object_name"], 
                        action='store', 
                        required=True)
    parser.add_argument('--object_id', 
                        help=script_details["Args"]["object_id"], 
                        action='store')

    # the types that we are transforming between, currently assumed one to one 
    parser.add_argument('--external_type', 
                        help=script_details["Args"]["external_type"], 
                        action='store', 
                        required=True)
    parser.add_argument('--kbase_type', 
                        help=script_details["Args"]["kbase_type"], 
                        action='store', 
                        required=True)

    # any user options provided, encoded as a jason string                           
    parser.add_argument('--optional_arguments', 
                        help=script_details["Args"]["optional_arguments"], 
                        action='store', 
                        default='{}')

    # Used if you are restarting a previously executed job?
    parser.add_argument('--ujs_job_id', 
                        help=script_details["Args"]["ujs_job_id"], 
                        action='store', 
                        default=None, 
                        required=False)

    # config information for running the validate and transform scripts
    parser.add_argument('--job_details', 
                        help=script_details["Args"]["job_details"], 
                        action='store', 
                        default=None)

    # the working directory is where all the files for this job will be written, 
    # and normal operation cleans it after the job ends (success or fail)
    parser.add_argument('--working_directory', 
                        help=script_details["Args"]["working_directory"], 
                        action='store', 
                        default=None, 
                        required=True)
    parser.add_argument('--keep_working_directory', 
                        help=script_details["Args"]["keep_working_directory"], 
                        action='store_true')
                        
    parser.add_argument('--debug', 
                        help=script_details["Args"]["debug"], 
                        action='store_true')

    # ignore any extra arguments
    args, unknown = parser.parse_known_args()
            
    kb_token = os.environ.get('KB_AUTH_TOKEN')
    ujs = UserAndJobState(url=args.ujs_service_url, token=kb_token)

    est = datetime.datetime.utcnow() + datetime.timedelta(hours=24)
    if args.ujs_job_id is not None:
        ujs.update_job_progress(args.ujs_job_id, kb_token, "KBase Data Upload started", 
                                1, est.strftime('%Y-%m-%dT%H:%M:%S+0000'))

    # parse all the json strings from the argument list into dicts
    # TODO had issues with json.loads and unicode strings, workaround was using simplejson
    
    args.url_mapping = simplejson.loads(base64.urlsafe_b64decode(args.url_mapping))
    args.optional_arguments = simplejson.loads(base64.urlsafe_b64decode(args.optional_arguments))
    args.job_details = simplejson.loads(base64.urlsafe_b64decode(args.job_details))

    logger.debug(args)

    if not os.path.exists(args.working_directory):
        os.mkdir(args.working_directory)

    # setup subdirectories to pass to subtasks for working directories
    download_directory = os.path.join(args.working_directory, "user_external")
    validation_directory = os.path.join(args.working_directory, "validation")
    transform_directory = os.path.join(args.working_directory, "objects")

    if args.ujs_job_id is not None:
        ujs.update_job_progress(args.ujs_job_id, kb_token, 
                                "Downloading input data from {0}".format(args.url_mapping), 
                                1, est.strftime('%Y-%m-%dT%H:%M:%S+0000') )

    # Step 1 : Download the data to disk
    try:
        os.mkdir(download_directory)
        script_utils.download_from_urls(logger, working_directory=download_directory, 
                                        urls=args.url_mapping, token=kb_token)
    except Exception, e:
        handler_utils.report_exception(logger, 
                         {"message": 'ERROR : Input data download from {0}'.format(args.url_mapping),
                          "exc": e,
                          "ujs": ujs,
                          "ujs_job_id": args.ujs_job_id,
                          "token": kb_token,
                         },
                         {"keep_working_directory": args.keep_working_directory,
                          "working_directory": args.working_directory})

        ujs.complete_job(args.ujs_job_id, 
                         kb_token, 
                         "Upload to {0} failed.".format(args.workspace_name), 
                         e, 
                         None)                                  


    # Report progress on success of the download step
    if args.ujs_job_id is not None:
        ujs.update_job_progress(args.ujs_job_id, kb_token, "Input data download completed", 
                                1, est.strftime('%Y-%m-%dT%H:%M:%S+0000'))

    logger.info(str(args))

    # Step 2 : Validate the data files, if there is a separate validation script
    if not args.job_details["transform"]["handler_options"].has_key("must_own_validation") or \
        args.job_details["transform"]["handler_options"]["must_own_validation"] == 'false':        
        try:
            os.mkdir(validation_directory)
    
            validation_args = args.job_details["validate"]
            
            # optional argument
            if "optional_fields" in validation_args["handler_options"]: 
                for k in args.optional_arguments["validate"]:
                    if k in validation_args["handler_options"]["optional_fields"]:
                        validation_args[k] = args.optional_arguments["validate"][k]

            # custom argument
            if "custom_options" in validation_args["handler_options"]: 
                for c in validation_args["handler_options"]["custom_options"]:
                    if c["type"] != "boolean":
                        validation_args[c["name"]] = c["value"]
                    else:
                        validation_args[c["name"]] = c["value"] # TODO: Fix later with example
        
            # gather a list of all files downloaded
            files = list(handler_utils.gen_recursive_filelist(download_directory))
    
            # get the directories common to those files
            directories = list()
            for x in files:
                path = os.path.dirname(x)
        
                if path not in directories:
                    directories.append(path)
        
            # validate everything in each directory
            # TODO: 1) The following logic assume all the same type and 
            #          it will be broken if there are multiple types
            #       2) input_directory assume it can handle files without input_mapping        
            validation_fields = validation_args["handler_options"]["required_fields"][:]
            validation_fields.extend(validation_args["handler_options"]["optional_fields"])
        
            for d in directories:
                if "input_directory" in validation_fields: 
                    validation_args["input_directory"] = d
                
                if "working_directory" in validation_fields:
                    validation_args["working_directory"] = validation_directory
                
                if "input_file_name" in validation_fields:
                    files = os.listdir(d)
                
                    if len(files) == 1:
                        validation_args["input_file_name"] = os.path.join(d,files[0])
                    else:
                        raise Exception("Expecting one file for input_file_name, found {0}.".format(len(files)))
                        
                for k in args.optional_arguments["validate"]:
                    if k in validation_args["handler_options"]["required_fields"]:
                        validation_args[k] = args.optional_arguments["validate"][k]
                             
                for x in remove_keys:
                    if x in validation_args:
                        del validation_args[x]

                handler_utils.run_task(logger, validation_args)
        except Exception, e:
            handler_utils.report_exception(logger, 
                             {"message": "ERROR : Validation of {0}".format(args.url_mapping),
                              "exc": e,
                              "ujs": ujs,
                              "ujs_job_id": args.ujs_job_id,
                              "token": kb_token,
                             },
                             {"keep_working_directory": args.keep_working_directory,
                              "working_directory": args.working_directory})

            ujs.complete_job(args.ujs_job_id, 
                             kb_token, 
                             "Upload to {0} failed.".format(args.workspace_name), 
                             e, 
                             None)                                  


        # Report progress on success of validation step
        if args.ujs_job_id is not None:
            ujs.update_job_progress(args.ujs_job_id, kb_token, 'Input data has passed validation', 1, est.strftime('%Y-%m-%dT%H:%M:%S+0000'))


    # Step 3: Transform the data
    try:
        # build input_mapping from user args
        input_mapping = dict()
        for name in args.url_mapping:
            checkPath = os.path.join(download_directory, name)
            files = os.listdir(checkPath)
        
            if len(files) == 1:
                input_mapping[name] = os.path.abspath(os.path.join(checkPath, files[0]))
            else:
                input_mapping[name] = checkPath
    
    
        transformation_args = args.job_details["transform"]
        
        # optional argument
        if "optional_fields" in transformation_args["handler_options"]: 
            for k in args.optional_arguments["transform"]:
                if k in transformation_args["handler_options"]["optional_fields"]:
                    if k == "output_file_name":
                        transformation_args[k] = os.path.join(transform_directory, args.optional_arguments["transform"][k])
                    else: 
                        transformation_args[k] = args.optional_arguments["transform"][k]

        # custom argument
        if  "custom_options" in transformation_args["handler_options"]: 
            for c in transformation_args["handler_options"]["custom_options"]:
                if(c["type"] != "boolean"):
                    transformation_args[c["name"]] = c["value"]
                else:
                    transformation_args[c["name"]] = c["value"] # TODO: Fix later with example

        transformation_fields = transformation_args["handler_options"]["required_fields"][:]
        transformation_fields.extend(transformation_args["handler_options"]["optional_fields"])

        os.mkdir(transform_directory)            
        if "working_directory" in transformation_fields: 
            transformation_args["working_directory"] = transform_directory
        
        if "input_directory" in transformation_fields:
            transformation_args["input_directory"] = download_directory
        
        if "input_mapping" in transformation_fields:
            transformation_args["input_mapping"] = simplejson.dumps(input_mapping)

        #Need to process optional argument to be processed and converted to command arguments
        if "input_file_name" in transformation_fields:
            for k in transformation_args["handler_options"]["input_mapping"]:
                if k in input_mapping:
                    transformation_args["input_file_name"] = input_mapping[k]
        else:
            for k in transformation_args["handler_options"]["input_mapping"]:
                if k in input_mapping:
                    transformation_args[transformation_args["handler_options"]["input_mapping"][k]] = input_mapping[k]

        if "workspace_service_url" in transformation_fields: 
            transformation_args["workspace_service_url"] = args.workspace_service_url

        if "shock_service_url" in transformation_fields: 
            transformation_args["shock_service_url"] = args.shock_service_url
        
        if "handle_service_url" in transformation_fields: 
            transformation_args["handle_service_url"] = args.handle_service_url

        for k in args.optional_arguments["transform"]:
            if k in transformation_args["handler_options"]["required_fields"]:
                if k == "output_file_name":
                    transformation_args[k] = os.path.join(transform_directory, args.optional_arguments["transform"][k])
                else: 
                    transformation_args[k] = args.optional_arguments["transform"][k]

        for x in remove_keys:
            if x in transformation_args:
                del transformation_args[x]

        handler_utils.run_task(logger, transformation_args, debug=args.debug)
    except Exception, e:
        handler_utils.report_exception(logger, 
                         {"message": "ERROR : Creating an object from {0}".format(args.url_mapping),
                          "exc": e,
                          "ujs": ujs,
                          "ujs_job_id": args.ujs_job_id,
                          "token": kb_token,
                         },
                         {"keep_working_directory": args.keep_working_directory,
                          "working_directory": args.working_directory})

        ujs.complete_job(args.ujs_job_id, 
                         kb_token, 
                         "Upload to {0} failed.".format(args.workspace_name), 
                         e, 
                         None)                                  


    # Report progress on success of transform step
    if args.ujs_job_id is not None:
        ujs.update_job_progress(args.ujs_job_id, kb_token, 
                                'Data is in a KBase format, preparing to save...', 
                                1, est.strftime('%Y-%m-%dT%H:%M:%S+0000'))


    # Step 4: Save the data to the Workspace
    try:    
        files = os.listdir(transform_directory)
        
        for f in files:
            path = os.path.join(transform_directory, f)
            
            if os.path.isfile(path):
                object_details = dict()
                object_details["workspace_service_url"] = args.workspace_service_url
                object_details["workspace_name"] = args.workspace_name
                object_details["object_name"] = args.object_name
                object_details["kbase_type"] = args.kbase_type
                object_details["object_meta"] = {}
                object_details["provenance"] = [{"time": datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S+0000'),
                                                 "service": "KBase Transform",
                                                 "service_ver": "0.1",
                                                 "method": "upload",
                                                 "method_params": [args.kbase_type,
                                                                   args.external_type,
                                                                   args.workspace_name,
                                                                   args.object_name,
                                                                   args.url_mapping,
                                                                   args.optional_arguments],
                                                 "script": __file__,
                                                 "script_ver": "0.0.1",
                                                 "description": "KBase Upload"}]
                
                script_utils.save_json_to_workspace(logger = logger,
                                                    json_file = path,
                                                    workspace_service_url = args.workspace_service_url,
                                                    object_details = object_details,
                                                    token = kb_token)
                
                # Report progress on success of saving the object
                #if args.ujs_job_id is not None:
                #    ujs.update_job_progress(args.ujs_job_id, 
                #                            kb_token, 
                #                            "Saved object {0} to {1}".format(args.object_name, args.workspace_name), 
                #                            1, est.strftime('%Y-%m-%dT%H:%M:%S+0000'))
    except Exception, e:
        handler_utils.report_exception(logger, 
                         {"message": "ERROR : Saving object {0} to {1}".format(args.object_name, args.workspace_name),
                          "exc": e,
                          "ujs": ujs,
                          "ujs_job_id": args.ujs_job_id,
                          "token": kb_token,
                         },
                         {"keep_working_directory": args.keep_working_directory,
                          "working_directory": args.working_directory})

        ujs.complete_job(args.ujs_job_id, 
                         kb_token, 
                         "Upload to {0} failed.".format(args.workspace_name), 
                         e, 
                         None)                                  

    
    # Report progress on the overall task being completed
    if args.ujs_job_id is not None:
        ujs.complete_job(args.ujs_job_id, 
                         kb_token, 
                         "Upload to {0} completed".format(args.workspace_name), 
                         None, 
                         {"shocknodes" : [], 
                          "shockurl" : args.shock_service_url, 
                          "workspaceids" : [], 
                          "workspaceurl" : args.workspace_service_url,
                          "results" : [{"server_type" : "Workspace", 
                                        "url" : args.workspace_service_url, 
                                        "id" : "{}/{}".format(args.workspace_name, 
                                                              args.object_name), 
                                        "description" : "description"}]})
    
    # Almost done, remove the working directory if possible
    if not args.keep_working_directory:
        handler_utils.cleanup(logger, args.working_directory)

    sys.exit(0);

if __name__ == "__main__":
    main()    
