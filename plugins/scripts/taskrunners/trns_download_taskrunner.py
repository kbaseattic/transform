#!/usr/bin/env python

import sys
import os
import datetime
import logging
import argparse
import base64
import zipfile
import shutil

import simplejson

from biokbase.workspace.client import Workspace
from biokbase.userandjobstate.client import UserAndJobState
from biokbase.Transform import handler_utils
from biokbase.Transform import script_utils


def main():
    """
    KBase Download task manager for converting from KBase objects to external data formats.
    
    Step 1 - Convert the objects to local files
    Step 2 - Extract provenance and metadata
    Step 3 - Package all files into a tarball or zip
    Step 4 - Upload the compressed file to shock and return the download url

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
        workspace_name: The name of the source workspace.
        object_name: The source object name.
        object_id: A source object id, which can be used instead of object_name.
        external_type: The external data format being transformed to from a KBase type.
                       E.g., FASTA.DNA.Assembly
                       This is simply a string, but denotes the format of the data and
                       some context about what it actually is, which is used to 
                       differentiate between files of the same general format with
                       different fundamental values.                       
        kbase_type: The KBase Workspace type string that indicates the module and type
                    of the object being created.
        optional_arguments: This is a JSON string containing optional parameters that can
                            be passed in to customize behavior based on available 
                            exposed options.
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
        
        Actual data output is a shock url that contains data files that were created
        based on KBase objects.
        
    Authors:
        Shinjae Yoo, Matt Henderson            
    """

    logger = script_utils.stderrlogger(__file__, level=logging.DEBUG)
    
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

    # workspace info for pulling the data
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

    # config information for running subtasks such as transform scripts
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

    # ignore any extra arguments
    args, unknown = parser.parse_known_args()
            
    kb_token = os.environ.get('KB_AUTH_TOKEN')
    ujs = UserAndJobState(url=args.ujs_service_url, token=kb_token)

    est = datetime.datetime.utcnow() + datetime.timedelta(minutes=3)
    if args.ujs_job_id is not None:
        ujs.update_job_progress(args.ujs_job_id, kb_token, "KBase Data Download to external formats started", 
                                1, est.strftime('%Y-%m-%dT%H:%M:%S+0000'))

    logger.info("Executing KBase Download tasks")

    # parse all the json strings from the argument list into dicts
    # TODO had issues with json.loads and unicode strings, workaround was using simplejson and base64
    
    args.optional_arguments = simplejson.loads(base64.urlsafe_b64decode(args.optional_arguments))
    args.job_details = simplejson.loads(base64.urlsafe_b64decode(args.job_details))
    
    current_directory = os.getcwd()
    
    if not os.path.exists(args.working_directory):
        os.mkdir(args.working_directory)

    # setup subdirectories to pass to subtasks for working directories
    transform_directory = os.path.join(args.working_directory, "user_external")

    if args.ujs_job_id is not None:
        ujs.update_job_progress(args.ujs_job_id, kb_token, 
                                "Gathering workspace data from {0}".format(args.workspace_name), 
                                1, est.strftime('%Y-%m-%dT%H:%M:%S+0000'))

    # Step 1 : Call the transform task to convert the objects to local files
    try:
        os.mkdir(transform_directory)        
        os.chdir(transform_directory)

        logger.debug(args.optional_arguments)
        
        transformation_args = dict()
        transformation_args.update(args.job_details["transform"])
        
        logger.debug(transformation_args)
        
        # take in user options
        for k in args.optional_arguments["transform"]:
            if k in transformation_args["handler_options"]["required_fields"] or \
               k in transformation_args["handler_options"]["optional_fields"]:
                transformation_args[k] = args.optional_arguments["transform"][k]
            else:
                logger.warning("Unrecognized parameter {0}".format(k))

        # take in all taskrunner args
        for k in args.__dict__:
            if k in transformation_args["handler_options"]["required_fields"] or \
               k in transformation_args["handler_options"]["optional_fields"]:
                transformation_args[k] = args.__dict__[k]

        # take in any handler custom args
        if "custom_options" in transformation_args["handler_options"]: 
            for c in transformation_args["handler_options"]["custom_options"]:
                transformation_args[c["name"]] = c["value"]

        if "working_directory" in transformation_args: 
            logger.debug(os.path.abspath(os.getcwd()))
            transformation_args["working_directory"] = os.path.abspath(os.getcwd())

        if "workspace_service_url" in transformation_args: 
            transformation_args["workspace_service_url"] = args.workspace_service_url

        if "shock_service_url" in transformation_args: 
            transformation_args["shock_service_url"] = args.shock_service_url
        
        if "handle_service_url" in transformation_args: 
            transformation_args["handle_service_url"] = args.handle_service_url

        # clean out arguments passed to transform script
        remove_keys = ["handler_options", "user_options", "user_option_groups",
                       "developer_description", "user_description", 
                       "kbase_type", "external_type", "script_type"]

        # check that we are not missing any required arguments
        for k in transformation_args["handler_options"]["required_fields"]:
            if k not in transformation_args:
                raise Exception("Missing required field {0}, please provide using optional_arguments.".format(k))

        # remove any argument keys that should not be passed to the transform step
        for x in remove_keys:
            if x in transformation_args:
                del transformation_args[x]

        logger.debug(transformation_args)

        task_output = handler_utils.run_task(logger, transformation_args, debug=args.debug)
        
        if task_output["stdout"] is not None:
            logger.debug("STDOUT : " + str(task_output["stdout"]))
        
        if task_output["stderr"] is not None:
            logger.debug("STDERR : " + str(task_output["stderr"]))
        
        os.chdir(current_directory)        
    except Exception, e:
        os.chdir(current_directory)        

        handler_utils.report_exception(logger, 
                         {"message": 'ERROR : Transforming workspace data from {0}'.format(args.workspace_name),
                          "exc": e,
                          "ujs": ujs,
                          "ujs_job_id": args.ujs_job_id,
                          "token": kb_token,
                         },
                         {"keep_working_directory": args.keep_working_directory,
                          "working_directory": args.working_directory})

        ujs.complete_job(args.ujs_job_id, 
                         kb_token, 
                         "Transform from {0} failed.".format(args.workspace_name), 
                         e, 
                         None)                                  

    
    # Report progress on success of the download step
    if args.ujs_job_id is not None:
        ujs.update_job_progress(args.ujs_job_id, kb_token, "Workspace objects transformed to {0}".format(args.external_type), 
                                1, est.strftime('%Y-%m-%dT%H:%M:%S+0000'))


    # TODO check to see if a validator is configured, if not skip to transform
    # Step 2 : Validate the data files
#    try:
#        os.mkdir(validation_directory)
#    
#        validation_args = args.job_details["validate"]
#        validation_args["optional_arguments"] = args.optional_arguments
#        
#        # gather a list of all files downloaded
#        files = list(handler_utils.gen_recursive_filelist(download_directory))
#        
#        # get the directories common to those files
#        directories = list()
#        for x in files:
#            path = os.path.dirname(x)
#            
#            if path not in directories:
#                directories.append(path)
#        
#        # validate everything in each directory
#        for d in directories:
#            validation_args["input_directory"] = d
#            validation_args["working_directory"] = validation_directory
#            handler_utils.run_task(logger, validation_args)
#    except Exception, e:
#        handler_utils.report_exception(logger, 
#                         {"message": "ERROR : Validation of {0}".format(args.url_mapping),
#                          "exc": e,
#                          "ujs": ujs,
#                          "ujs_job_id": args.ujs_job_id,
#                          "token": kb_token,
#                         },
#                         {"keep_working_directory": args.keep_working_directory,
#                          "working_directory": args.working_directory})
#
#        ujs.complete_job(args.ujs_job_id, 
#                         kb_token, 
#                         "Upload to {0} failed.".format(args.workspace_name), 
#                         e, 
#                         None)                                  
#
#
#    # Report progress on success of validation step
#    if args.ujs_job_id is not None:
#        ujs.update_job_progress(args.ujs_job_id, kb_token, 'Input data has passed validation', 1, est.strftime('%Y-%m-%dT%H:%M:%S+0000') )



    # Step 2: Extract provenance and metadata
    try:    
        workspaceClient = Workspace(url=args.workspace_service_url, token=kb_token)
        
        object_info = {"workspace": args.workspace_name, "name": args.object_name}

        object_details = dict()
        object_details["provenance"] = workspaceClient.get_object_provenance([object_info])
        #object_details["history"] = workspaceClient.get_object_history(object_info)
        object_details["metadata"] = workspaceClient.get_object_info_new({"objects":[object_info], "includeMetadata":1})
        #object_details["references"] = workspaceClient.list_referencing_objects([object_info])
        
        object_metadata_filename = "KBase_object_details_{0}_{1}.json".format(args.object_name, datetime.datetime.utcnow().isoformat())
        file_name = os.path.join(transform_directory, object_metadata_filename)
        
        with open(file_name, 'w') as f:
            f.write(simplejson.dumps(object_details, sort_keys=True, indent=4))
    except Exception, e:
        handler_utils.report_exception(logger, 
                         {"message": "ERROR : Extracting metadata and provenance failed",
                          "exc": e,
                          "ujs": ujs,
                          "ujs_job_id": args.ujs_job_id,
                          "token": kb_token,
                         },
                         {"keep_working_directory": args.keep_working_directory,
                          "working_directory": args.working_directory})

        ujs.complete_job(args.ujs_job_id, 
                         kb_token, 
                         "Download from {0} failed.".format(args.workspace_name), 
                         e, 
                         None)                                  
    
    
    shock_id = None
    # Step 3: Package data files into a single compressed file and send to shock
    try:
        name = "KBase_{0}_{1}_to_{2}_{3}".format(args.object_name, args.kbase_type, args.external_type, datetime.datetime.utcnow().isoformat())

        # gather a list of all files downloaded
        files = list(handler_utils.gen_recursive_filelist(transform_directory))        
        
        archive_name = os.path.join(args.working_directory,name) + ".zip"
        archive = zipfile.ZipFile(archive_name, 'w', zipfile.ZIP_DEFLATED, allowZip64=True)
        for n in files:
            archive.write(n)
        archive.close()
        
        shock_info = script_utils.upload_file_to_shock(logger = logger,
                                                       shock_service_url = args.shock_service_url,
                                                       filePath = archive_name,
                                                       token= kb_token)
        shock_id = shock_info["id"]
    except Exception, e:
        handler_utils.report_exception(logger, 
                         {"message": "ERROR : Compressing files and saving to SHOCK failed",
                          "exc": e,
                          "ujs": ujs,
                          "ujs_job_id": args.ujs_job_id,
                          "token": kb_token,
                         },
                         {"keep_working_directory": args.keep_working_directory,
                          "working_directory": args.working_directory})

        ujs.complete_job(args.ujs_job_id, 
                         kb_token, 
                         "Download from {0} failed.".format(args.workspace_name), 
                         e, 
                         None)                                  

    
    # Report progress on the overall task being completed
    if args.ujs_job_id is not None:
        ujs.complete_job(args.ujs_job_id, 
                         kb_token, 
                         "Download from {0} completed".format(args.workspace_name), 
                         None, 
                         {"shocknodes" : ["{0}/node/{1}?download_raw".format(args.shock_service_url,shock_id)], 
                          "shockurl" : args.shock_service_url, 
                          "results" : [{"server_type" : "Shock", 
                                        "url" : "{0}/node/{1}?download_raw".format(args.shock_service_url,shock_id), 
                                        "id" : shock_id,
                                        "description": "Download"}]})
    
    # Almost done, remove the working directory if possible
    if not args.keep_working_directory:
        handler_utils.cleanup(logger, args.working_directory)

    sys.exit(0);

if __name__ == "__main__":
    main()    
