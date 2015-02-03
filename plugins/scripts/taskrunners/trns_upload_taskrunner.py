#!/usr/bin/env python

import sys
import os
import datetime
import logging
import argparse
import base64
import traceback

import simplejson

from biokbase.workspace.client import Workspace
from biokbase.userandjobstate.client import UserAndJobState
import biokbase.Transform.handler_utils as handler_utils
import biokbase.Transform.script_utils as script_utils


def upload_taskrunner(ujs_service_url = None, workspace_service_url = None,
                      shock_service_url = None, handle_service_url = None,
                      fba_service_url = None, url_mapping = None,
                      workspace_name = None, object_name = None,
                      object_id = None, external_type = None,
                      kbase_type = None, optional_arguments = None,
                      ujs_job_id = None, job_details = None,
                      working_directory = None, keep_working_directory = None,
                      debug = False, logger = None):
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
        fba_service_url: URL for a KBase FBA Model service that has to handle any
                         model related conversions.
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
        One or more Workspace objects saved to a user's workspace 
        based on input files provided by urls.
        
    Authors:
        Shinjae Yoo, Matt Henderson            
    """

    # validate inputs and environment
    if logger is None:
        raise Exception("A logger must be provided for status information.")
    
    kb_token = None
    try:                
        kb_token = script_utils.get_token()
        
        assert type(kb_token) == type(str())
    except Exception, e:
        logger.debug("Unable to get token!")
        logger.exception(e)
        sys.exit(1)

    ujs = None
    try:
        if ujs_job_id is not None:
            ujs = UserAndJobState(url=ujs_service_url, token=kb_token)
            ujs.get_job_status(ujs_job_id)
    except Exception, e:
        logger.debug("Unable to connect to UJS service!")
        raise

    # used for cleaning up the job if an exception occurs
    cleanup_details = {"keep_working_directory": keep_working_directory,
                       "working_directory": working_directory}

    # used for reporting a fatal condition
    error_object = {"status": "error",
                    "ujs_client": ujs,
                    "ujs_job_id": ujs_job_id,
                    "token": kb_token}

    est = datetime.datetime.utcnow() + datetime.timedelta(hours=24)
    try:
        if ujs_job_id is not None:
            ujs.update_job_progress(ujs_job_id, kb_token, "KBase Data Upload started", 
                                    1, est.strftime('%Y-%m-%dT%H:%M:%S+0000'))
        else:
            logger.info("KBase Data Upload started")

        if not os.path.exists(working_directory):
            os.mkdir(working_directory)

        # setup subdirectories to pass to subtasks for working directories
        download_directory = os.path.join(working_directory, "user_external")
        validation_directory = os.path.join(working_directory, "validation")
        transform_directory = os.path.join(working_directory, "objects")

        if ujs_job_id is not None:
            ujs.update_job_progress(ujs_job_id, kb_token, 
                                    "Downloading input data", 
                                    1, est.strftime('%Y-%m-%dT%H:%M:%S+0000'))
        else:
            logger.info("Downloading input data")

        
        # Step 1 : Download the data to disk
        try:
            os.mkdir(download_directory)
            script_utils.download_from_urls(logger, 
                                            working_directory=download_directory, 
                                            urls=url_mapping, 
                                            token=kb_token)
        except Exception, e:
            logger.debug("Caught exception while downloading the data files!")
            
            if ujs_job_id is not None:
                #error_object["status"] = "ERROR : Input data download - {0}".format(e.message)[:handler_utils.UJS_STATUS_MAX]
                error_object["error_message"] = traceback.format_exc()
                
                handler_utils.report_exception(logger, error_object, cleanup_details)

                ujs.complete_job(ujs_job_id, 
                                 kb_token, 
                                 "Upload to {0} failed.".format(workspace_name), 
                                 traceback.format_exc(), 
                                 None)
                
                sys.exit(1)
            else:
                logger.error("Input data download")
                logger.error("Upload to {0} failed.".format(workspace_name))
                raise

        # Report progress on success of the download step
        if ujs_job_id is not None:
            ujs.update_job_progress(ujs_job_id, kb_token, "Input data download completed", 
                                    1, est.strftime('%Y-%m-%dT%H:%M:%S+0000'))
        else:
            logger.info("Input data download completed")            

        logger.debug(job_details)

        # Step 2 : Validate the data files, if there is a separate validation script
        if not job_details["transform"]["handler_options"].has_key("must_own_validation") or \
           not job_details["transform"]["handler_options"]["must_own_validation"]:        
            try:
                if ujs_job_id is not None:
                    ujs.update_job_progress(ujs_job_id, kb_token, "Validation started", 
                                            1, est.strftime('%Y-%m-%dT%H:%M:%S+0000'))
                else:
                    logger.info("Validation started")            

                os.mkdir(validation_directory)
    
                validation_args = dict()
                validation_args["script_name"] = job_details["validate"]["script_name"]
                
                # cerate a placeholder for every required field
                for k in job_details["validate"]["handler_options"]["required_fields"]:
                    validation_args[k] = None
            
                # fill in any optional arguments provided by the user
                if "optional_fields" in job_details["validate"]["handler_options"]: 
                    for k in optional_arguments["validate"]:
                        if k in job_details["validate"]["handler_options"]["optional_fields"]:
                            validation_args[k] = optional_arguments["validate"][k]

                # fill in any custom options needed to run the script
                if "custom_options" in job_details["validate"]["handler_options"]: 
                    for c in job_details["validate"]["handler_options"]["custom_options"]:
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
        
                # TODO: 1) The following logic assumes all files are of the same type 
                #          and will not work properly if there are multiple file types
                #       2) input_directory assumes the script can handle files without 
                #          using input_mapping        
                #
                # validate everything in each directory
                for d in directories:
                    if "input_directory" in validation_args: 
                        validation_args["input_directory"] = d
                
                    if "working_directory" in validation_args:
                        validation_args["working_directory"] = validation_directory
                
                    if "input_file_name" in validation_args:
                        files = os.listdir(d)
                
                        if len(files) == 1:
                            validation_args["input_file_name"] = os.path.join(d,files[0])
                        else:
                            raise Exception("Expecting one file for input_file_name, found {0:d}.".format(len(files)))
                        
                    for k in optional_arguments["validate"]:
                        if k in job_details["handler_options"]["required_fields"]:
                            validation_args[k] = optional_arguments["validate"][k]

                    # check that we are not missing any required arguments
                    for k in job_details["validate"]["handler_options"]["required_fields"]:
                        if k not in validation_args:
                            raise Exception("Missing required field {0}, please provide using optional_arguments.".format(k))
                        elif validation_args[k] is None:
                            raise Exception("Missing value for required field {0}, please provide using optional_arguments.".format(k))

                    filename = os.path.split(files[0])[-1]

                    if ujs_job_id is not None:
                        # Update on validation steps
                        ujs.update_job_progress(ujs_job_id, kb_token, "Attempting to validate {0}".format(filename)[:handler_utils.UJS_STATUS_MAX], 
                                                1, est.strftime('%Y-%m-%dT%H:%M:%S+0000'))
                    else:
                        logger.info("Attempting to validate {0}".format(filename))

                    task_output = handler_utils.run_task(logger, validation_args)
                
                    if task_output["stdout"] is not None:
                        logger.debug("STDOUT : " + str(task_output["stdout"]))
        
                    if task_output["stderr"] is not None:
                        logger.debug("STDERR : " + str(task_output["stderr"]))        

                    if ujs_job_id is not None:
                        # Update on validation steps
                        ujs.update_job_progress(ujs_job_id, kb_token, "Validation completed on {0}".format(filename)[:handler_utils.UJS_STATUS_MAX], 
                                                1, est.strftime('%Y-%m-%dT%H:%M:%S+0000'))
                    else:
                        logger.info("Validation completed on {0}".format(filename))
            except Exception, e:
                logger.debug("Caught exception while validating!")

                if ujs_job_id is not None:
                    #error_object["status"] = "ERROR : Validation of input data - {0}".format(e.message)[:handler_utils.UJS_STATUS_MAX]
                    error_object["error_message"] = traceback.format_exc()
                
                    handler_utils.report_exception(logger, error_object, cleanup_details)

                    ujs.complete_job(ujs_job_id, 
                                     kb_token, 
                                     "Upload to {0} failed.".format(workspace_name), 
                                     traceback.format_exc(), 
                                     None)
                    sys.exit(1)
                else:
                    logger.error("Validation of input data")
                    logger.error("Upload to {0} failed.".format(workspace_name))
                    raise


            # Report progress on success of validation step
            if ujs_job_id is not None:
                ujs.update_job_progress(ujs_job_id, kb_token, 'Input data has passed validation', 1, est.strftime('%Y-%m-%dT%H:%M:%S+0000'))
            else:
                logger.info("Input data has passed validation")
        else:
            if ujs_job_id is not None:
                ujs.update_job_progress(ujs_job_id, kb_token, 'Validation not available, skipping.', 1, est.strftime('%Y-%m-%dT%H:%M:%S+0000'))
            else:
                logger.warning("Validation not available, skipping.")


        # Report progress of transformation about to begin
        if ujs_job_id is not None:
            ujs.update_job_progress(ujs_job_id, kb_token, 'Performing data transformation to KBase', 1, est.strftime('%Y-%m-%dT%H:%M:%S+0000'))
        else:
            logger.info("Performing data transformation to KBase")

        
        # Step 3: Transform the data
        try:
            copy_fields = dict()
            copy_fields["workspace_service_url"] = workspace_service_url
            copy_fields["shock_service_url"] = shock_service_url
            copy_fields["handle_service_url"] = handle_service_url
            copy_fields["fba_service_url"] = fba_service_url
            copy_fields["workspace_name"] = workspace_name
            copy_fields["object_name"] = object_name
            copy_fields["object_id"] = object_id     

            # build the argument set    
            transformation_args = dict()
            transformation_args["script_name"] = job_details["transform"]["script_name"]

            # get all required fields in set to None
            for k in job_details["transform"]["handler_options"]["required_fields"]:
                transformation_args[k] = None
                        
            # get any user specified options
            for k in optional_arguments["transform"]:
                if k in job_details["transform"]["handler_options"]["required_fields"] or \
                   k in job_details["transform"]["handler_options"]["optional_fields"]:
                    transformation_args[k] = optional_arguments["transform"][k]
                else:
                    logger.warning("Unrecognized parameter {0}".format(k))

            # get any argument values passed into the taskrunner
            for k in copy_fields:
                if k in job_details["transform"]["handler_options"]["required_fields"] or \
                   k in job_details["transform"]["handler_options"]["optional_fields"]:
                    transformation_args[k] = copy_fields[k]

            # get any specified custom args
            if "custom_options" in job_details["transform"]["handler_options"]: 
                for c in job_details["transform"]["handler_options"]["custom_options"]:
                    transformation_args[c["name"]] = c["value"]

            if "output_file_name" in transformation_args:
                transformation_args["output_file_name"] = os.path.join(transform_directory, transformation_args["output_file_name"])

            if "working_directory" in transformation_args: 
                transformation_args["working_directory"] = transform_directory

            if "input_directory" in transformation_args:
                transformation_args["input_directory"] = download_directory
                
            if "input_file_name" in transformation_args:
                transformation_args["input_file_name"] = list()

            # build input_mapping from user args
            input_mapping = dict()
            for name in url_mapping:
                checkPath = os.path.join(download_directory, name)
                files = os.listdir(checkPath)
    
                if job_details["transform"]["handler_options"]["input_mapping"][name] == "input_directory":
                    input_mapping[name] = checkPath
                else:
                    # if there is only one file, set that, otherwise assume directory
                    if len(files) == 1:
                        input_mapping[name] = os.path.abspath(os.path.join(checkPath, files[0]))
                    else:
                        input_mapping[name] = checkPath

            if "input_mapping" in transformation_args:
                transformation_args["input_mapping"] = simplejson.dumps(input_mapping)
            
            # fill out the arguments specified in the input mapping as keys
            for k in job_details["transform"]["handler_options"]["input_mapping"]:
                if k in input_mapping:
                    if job_details["transform"]["handler_options"]["input_mapping"][k] == "input_file_name":
                        transformation_args["input_file_name"].append(input_mapping[k])
                    else:
                        transformation_args[job_details["transform"]["handler_options"]["input_mapping"][k]] = input_mapping[k]

            # check that we are not missing any required arguments
            for k in job_details["transform"]["handler_options"]["required_fields"]:
                if k not in transformation_args:
                    raise Exception("Missing required field {0}, please provide using optional_arguments.".format(k))
                elif transformation_args[k] is None:
                    raise Exception("Missing value for required field {0}, please provide using optional_arguments.".format(k))

            logger.debug(transformation_args)
            os.mkdir(transform_directory)            

            task_output = handler_utils.run_task(logger, transformation_args, debug=debug)
        
            if task_output["stdout"] is not None:
                logger.debug("STDOUT : " + str(task_output["stdout"]))
        
            if task_output["stderr"] is not None:
                logger.debug("STDERR : " + str(task_output["stderr"]))        
        except Exception, e:
            logger.debug("Caught exception while saving the object!")
        
            if ujs_job_id is not None:
                #error_object["status"] = "ERROR : Creating objects - {0}".format(e.message)[:handler_utils.UJS_STATUS_MAX]
                error_object["error_message"] = traceback.format_exc()
            
                handler_utils.report_exception(logger, error_object, cleanup_details)

                ujs.complete_job(ujs_job_id, 
                                 kb_token, 
                                 "Upload to {0} failed.".format(workspace_name)[:handler_utils.UJS_STATUS_MAX], 
                                 traceback.format_exc(), 
                                 None)     
                sys.exit(1)                             
            else:
                logger.error("Creating an object from {0}".format(url_mapping))
                logger.error("Upload to {0} failed.".format(workspace_name))
                raise


        logger.debug(job_details["transform"]["handler_options"])

        # Step 4: Save the data to the Workspace
        if not job_details["transform"]["handler_options"].has_key("must_own_saving_to_workspace") or \
           not job_details["transform"]["handler_options"]["must_own_saving_to_workspace"]:        

            # Report progress on success of transform step
            if ujs_job_id is not None:
                ujs.update_job_progress(ujs_job_id, kb_token, 
                                        'Data is in a KBase format, preparing to save...', 
                                        1, est.strftime('%Y-%m-%dT%H:%M:%S+0000'))
            else:
                logger.info("Data is in a KBase format, preparing to save...")

            try:    
                files = os.listdir(transform_directory)
        
                for f in files:
                    path = os.path.join(transform_directory, f)
            
                    if os.path.isfile(path):
                        object_details = dict()
                        object_details["workspace_service_url"] = workspace_service_url
                        object_details["workspace_name"] = workspace_name
                        object_details["object_name"] = object_name
                        object_details["kbase_type"] = kbase_type
                        object_details["object_meta"] = {}
                        object_details["provenance"] = [{
                            "time": datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S+0000'),
                            "service": "KBase Transform",
                            "service_ver": "0.1",
                            "method": "upload",
                            "method_params": [kbase_type,
                                              external_type,
                                              workspace_name,
                                              object_name,
                                              url_mapping,
                                              optional_arguments],
                            "script": __file__,
                            "script_ver": "0.0.1",
                            "description": "KBase Upload"}]
                
                        script_utils.save_json_to_workspace(logger = logger,
                                                            json_file = path,
                                                            workspace_service_url = workspace_service_url,
                                                            object_details = object_details,
                                                            token = kb_token)
                
                        # Report progress on success of saving the object
                        if ujs_job_id is not None:
                            ujs.update_job_progress(ujs_job_id, 
                                                    kb_token, 
                                                    "Saved object {0} to {1}".format(object_name, workspace_name)[:handler_utils.UJS_STATUS_MAX], 
                                                    1, est.strftime('%Y-%m-%dT%H:%M:%S+0000'))
                        else:
                            logger.info("Saved object {0} to {1}".format(object_name, workspace_name))
                        
            except Exception, e:
                logger.debug("Caught exception while trying to save objects!")
                
                if ujs_job_id is not None:
                    #error_object["status"] = "ERROR : Saving object {0} to {1} - {2}".format(object_name, workspace_name, e.message)[:handler_utils.UJS_STATUS_MAX]
                    error_object["error_message"] = traceback.format_exc()
            
                    handler_utils.report_exception(logger, error_object, cleanup_details)

                    ujs.complete_job(ujs_job_id, 
                                     kb_token, 
                                     "Upload to {0} failed.".format(workspace_name), 
                                     traceback.format_exc(), 
                                     None)                                  
                    sys.exit(1)
                else:
                    logger.error("Saving object {0} to {1}".format(object_name, workspace_name))
                    logger.error("Upload to {0} failed.".format(workspace_name))
                    raise                    
    
            if ujs_job_id is not None:
                ujs.update_job_progress(ujs_job_id, kb_token, 
                                        'Objects saved to {0}'.format(workspace_name)[:handler_utils.UJS_STATUS_MAX], 
                                        1, est.strftime('%Y-%m-%dT%H:%M:%S+0000'))
            else:
                logger.info("Objects saved to {0}".format(workspace_name))
            
        else:
            # Report progress on success of transform step
            if ujs_job_id is not None:
                ujs.update_job_progress(ujs_job_id, kb_token, 
                                        'Data is in a KBase format and objects saved to {0}'.format(workspace_name)[:handler_utils.UJS_STATUS_MAX], 
                                        1, est.strftime('%Y-%m-%dT%H:%M:%S+0000'))
            else:
                logger.info("Data is in a KBase format and objects saved to {0}".format(workspace_name))
        
    
        # Report progress on the overall task being completed
        if ujs_job_id is not None:
            ujs.complete_job(ujs_job_id, 
                             kb_token, 
                             "Upload to {0} completed".format(workspace_name)[:handler_utils.UJS_STATUS_MAX], 
                             None, 
                             {"shocknodes" : [], 
                              "shockurl" : shock_service_url, 
                              "workspaceids" : [], 
                              "workspaceurl" : workspace_service_url,
                              "results" : [{"server_type" : "Workspace", 
                                            "url" : workspace_service_url, 
                                            "id" : "{}/{}".format(workspace_name, 
                                                                  object_name), 
                                            "description" : "description"}]})
        else:
            logger.info("Upload to {0} completed".format(workspace_name))
    
        # Almost done, remove the working directory if possible
        if not keep_working_directory:
            handler_utils.cleanup(logger, working_directory)

    except Exception, e:
        if ujs is None or ujs_job_id is None:
            raise

        logger.debug("Caught global exception!")
        
        # handle global exception
        error_object["status"] = "ERROR : Upload exited with : {0}".format(e.message)[:handler_utils.UJS_STATUS_MAX]
        error_object["error_message"] = traceback.format_exc()

        handler_utils.report_exception(logger, error_object, cleanup_details)

        ujs.complete_job(ujs_job_id, 
                         kb_token, 
                         "Upload to {0} failed.".format(workspace_name), 
                         traceback.format_exc(), 
                         None)
        raise                                  




if __name__ == "__main__":
    logger = script_utils.stderrlogger(__file__)    
    script_details = script_utils.parse_docs(upload_taskrunner.__doc__)
        
    parser = script_utils.ArgumentParser(description=script_details["Description"],
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

    parser.add_argument('--fba_service_url', 
                        help=script_details["Args"]["fba_service_url"], 
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
                        
    # turn on debugging options for script developers running locally
    parser.add_argument('--debug', 
                        help=script_details["Args"]["debug"], 
                        action='store_true')

    args = None
    try:
        args = parser.parse_args()        
    except Exception, e:
        logger.debug("Caught exception parsing arguments!")
        logger.exception(e)
        sys.exit(1)
    
    if not args.debug:
        # parse all the json strings from the argument list into dicts
        # TODO had issues with json.loads and unicode strings, workaround was using simplejson and base64
        try:
            args.url_mapping = simplejson.loads(base64.urlsafe_b64decode(args.url_mapping))
            args.optional_arguments = simplejson.loads(base64.urlsafe_b64decode(args.optional_arguments))
            args.job_details = simplejson.loads(base64.urlsafe_b64decode(args.job_details))
        except Exception, e:
            logger.debug("Exception while loading base64 json strings!")
            sys.exit(1)

    try:
        upload_taskrunner(ujs_service_url = args.ujs_service_url,
                          workspace_service_url = args.workspace_service_url,
                          shock_service_url = args.shock_service_url,
                          handle_service_url = args.handle_service_url,
                          fba_service_url = args.fba_service_url,
                          url_mapping = args.url_mapping,
                          workspace_name = args.workspace_name,
                          object_name = args.object_name,
                          object_id = args.object_id,
                          external_type = args.external_type,
                          kbase_type = args.kbase_type,
                          optional_arguments = args.optional_arguments,
                          ujs_job_id = args.ujs_job_id,
                          job_details = args.job_details,
                          working_directory = args.working_directory,
                          keep_working_directory = args.keep_working_directory,
                          debug = args.debug,
                          logger = logger)
    except Exception, e:
        logger.debug("Upload taskrunner threw an exception!")
        logger.exception(e)
        
        ujs = UserAndJobState(url=args.ujs_service_url, token=os.environ.get("KB_AUTH_TOKEN"))
        ujs.complete_job(args.ujs_job_id, 
                         os.environ.get("KB_AUTH_TOKEN"), 
                         e.message[:handler_utils.UJS_STATUS_MAX], 
                         traceback.format_exc(), 
                         None)
        sys.exit(1)
    
    logger.debug("Upload taskrunner completed, exiting normally.")
    sys.exit(0)        
