#!/usr/bin/env python

import sys
import os
import datetime
import logging
import argparse
import base64
import traceback
import tarfile
import zipfile
import shutil
import struct

import simplejson

from biokbase.workspace.client import Workspace
from biokbase.userandjobstate.client import UserAndJobState
import biokbase.Transform.handler_utils as handler_utils
import biokbase.Transform.script_utils as script_utils


def download_taskrunner(ujs_service_url = None, workspace_service_url = None,
                        shock_service_url = None, handle_service_url = None,
                        fba_service_url = None, workspace_name = None,
                        object_name = None, object_id = None,
                        external_type = None, kbase_type = None,
                        optional_arguments = None, ujs_job_id = None,
                        job_details = None, working_directory = None,
                        keep_working_directory = False, debug = False,
                        logger = None):
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
        fba_service_url: URL for the FBA Model service used by Model related types.
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

    if logger is None:
        raise Exception("A logger must be provided for status information.")

    kb_token = None
    try:            
        kb_token = script_utils.get_token()
        
        assert type(kb_token) == type(str())
    except Exception, e:
        logger.debug("Exception getting token!")
        raise

    ujs = None    
    try:
        if ujs_job_id is not None:    
            ujs = UserAndJobState(url=ujs_service_url, token=kb_token)
            ujs.get_job_status(ujs_job_id)
    except Exception, e:
        logger.debug("Exception talking to UJS!")
        raise

    # used for cleaning up the job if an exception occurs
    cleanup_details = {"keep_working_directory": keep_working_directory,
                       "working_directory": working_directory}

    # used for reporting a fatal condition
    error_object = {"ujs_client": ujs,
                    "ujs_job_id": ujs_job_id,
                    "token": kb_token}

    est = datetime.datetime.utcnow() + datetime.timedelta(hours=24)
    try:
        if ujs_job_id is not None:
            ujs.update_job_progress(ujs_job_id, kb_token, "KBase Data Download to external formats started", 
                                    1, est.strftime('%Y-%m-%dT%H:%M:%S+0000'))
        else:
            logger.info("KBase Data Download to external formats started")

        logger.info("Executing KBase Download tasks")

        current_directory = os.getcwd()
    
        if not os.path.exists(working_directory):
            os.mkdir(working_directory)

        # setup subdirectories to pass to subtasks for working directories
        transform_directory = os.path.join(working_directory, "user_external")

        if ujs_job_id is not None:
            ujs.update_job_progress(ujs_job_id, kb_token, 
                                    "Gathering workspace data from {0}".format(workspace_name)[:handler_utils.UJS_STATUS_MAX], 
                                    1, est.strftime('%Y-%m-%dT%H:%M:%S+0000'))
        else:
            logger.info("Gathering workspace data from {0}".format(workspace_name))

        # Step 1 : Call the transform task to convert the objects to local files
        try:
            os.mkdir(transform_directory)        
            os.chdir(transform_directory)

            logger.debug(optional_arguments)

            copy_fields = dict()
            copy_fields["workspace_service_url"] = workspace_service_url
            copy_fields["shock_service_url"] = shock_service_url
            copy_fields["handle_service_url"] = handle_service_url
            copy_fields["fba_service_url"] = fba_service_url
            copy_fields["workspace_name"] = workspace_name
            copy_fields["object_name"] = object_name
            copy_fields["object_id"] = object_id     
        
            transformation_args = dict()
            transformation_args["script_name"] = job_details["transform"]["script_name"]
            
            # make sure all required fields get an entry            
            for k in job_details["transform"]["handler_options"]["required_fields"]:
                transformation_args[k] = None
            
            # take in user options
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

            # take in any handler custom args
            if "custom_options" in job_details["transform"]["handler_options"]: 
                for c in job_details["transform"]["handler_options"]["custom_options"]:
                    transformation_args[c["name"]] = c["value"]

            if "working_directory" in transformation_args: 
                logger.debug(os.path.abspath(os.getcwd()))
                transformation_args["working_directory"] = os.path.abspath(os.getcwd())

            # check that we are not missing any required arguments
            for k in job_details["transform"]["handler_options"]["required_fields"]:
                if transformation_args[k] is None:
                    raise Exception("Missing required field {0}, please provide using optional_arguments.".format(k))

            logger.debug(transformation_args)

            task_output = handler_utils.run_task(logger, transformation_args, debug=debug)
        
            if task_output["stdout"] is not None:
                logger.debug("STDOUT : " + str(task_output["stdout"]))
        
            if task_output["stderr"] is not None:
                logger.debug("STDERR : " + str(task_output["stderr"]))
        
            os.chdir(current_directory)        
        except Exception, e:
            logger.debug("Caught exception during transformation step!")
            
            os.chdir(current_directory)        

            if ujs_job_id is not None:
                error_object["status"] = "ERROR : Transformation from KBase type to External type failed - {0}".format(e.message)[:handler_utils.UJS_STATUS_MAX]
                error_object["error_message"] = traceback.format_exc()
            
                handler_utils.report_exception(logger, error_object, cleanup_details)

                ujs.complete_job(ujs_job_id, 
                                 kb_token, 
                                 "Transform from {0} failed.".format(workspace_name), 
                                 traceback.format_exc(), 
                                 None)
                sys.exit(1)
            else:
                logger.error("Conversion of data to workspace object")
                logger.error("Download from {0} failed.".format(workspace_name))
                raise

        # Report progress on success of the download step
        if ujs_job_id is not None:
            ujs.update_job_progress(ujs_job_id, kb_token, "Workspace objects transformed to {0}".format(external_type)[:handler_utils.UJS_STATUS_MAX], 
                                    1, est.strftime('%Y-%m-%dT%H:%M:%S+0000'))
        else:
            logger.info("Workspace objects transformed to {0}".format(external_type))

        #
        # TODO validation of data files after transform
        #

        # Step 2: Extract provenance and metadata
        try:    
            workspaceClient = Workspace(url=workspace_service_url, token=kb_token)
        
            object_info = {"workspace": workspace_name, "name": object_name}

            object_details = dict()
            object_details["provenance"] = workspaceClient.get_object_provenance([object_info])
            object_details["metadata"] = workspaceClient.get_object_info_new({"objects":[object_info], "includeMetadata":1})
            
            #logger.debug(object_details["metadata"])
            
            # redundant information
            #object_details["references"] = workspaceClient.list_referencing_objects([object_info])

            # seems like maybe too crazy per download
            #object_details["history"] = workspaceClient.get_object_history(object_info)

            object_version = object_details["metadata"][0][4]
        
            object_metadata_filename = "KBase_object_details_{0}_{1}_v{2}.json".format(workspace_name, object_name, object_version)
            file_name = os.path.join(transform_directory, object_metadata_filename)
        
            with open(file_name, 'w') as f:
                f.write(simplejson.dumps(object_details, sort_keys=True, indent=4))
        except Exception, e:
            if ujs_job_id is not None:
                error_object["status"] = "ERROR : Extracting provenance and metadata failed - {0}".format(e.message)[:handler_utils.UJS_STATUS_MAX]
                error_object["error_message"] = traceback.format_exc()
            
                handler_utils.report_exception(logger, error_object, cleanup_details)

                ujs.complete_job(ujs_job_id, 
                                 kb_token, 
                                 "Download from {0} failed.".format(workspace_name), 
                                 traceback.format_exc(), 
                                 None)
                sys.exit(1)
            else:
                logger.error("Extracting metadata and provenance failed")
                raise
    
    
        shock_id = None
        # Step 3: Package data files into a single compressed file and send to shock
        try:
            workspace_id = object_details["metadata"][0][4]
            object_version = object_details["metadata"][0][2]

            name = "KBase_{0}_{1}_{2}".format(workspace_name, object_name, object_version)

            # gather a list of all files downloaded
            files = list(handler_utils.gen_recursive_filelist(transform_directory))

            # gather total size of all files
            total = 0
            for x in files:
                total += os.path.getsize(x)

            # TODO
            # Workaround for Python 2.7.3 bug 9720, http://bugs.python.org/issue9720
            # The awe workers and KBase V26 are at Python 2.7.3 and we should migrate
            # to the same version of Python that Narrative uses, which is currently
            # Python 2.7.6, after which this workaround can be removed                    
            if total < 2**31:
                archive_name = os.path.join(working_directory, name) + ".zip"
                with zipfile.ZipFile(archive_name, 'w', zipfile.ZIP_DEFLATED) as archive:
                    for n in files:
                        archive.write(n, arcname=os.path.join(name, n.split(transform_directory + os.sep)[1]))
            else:
                archive_name = os.path.join(working_directory, name) + ".tar.bz2"
                with tarfile.open(archive_name, 'w:bz2') as archive:
                    for n in files:
                        archive.add(n, arcname=os.path.join(name, n.split(transform_directory + os.sep)[1]))
                
        
            shock_info = script_utils.upload_file_to_shock(logger = logger,
                                                           shock_service_url = shock_service_url,
                                                           filePath = archive_name,
                                                           token= kb_token)
            shock_id = shock_info["id"]
        except Exception, e:
            logger.debug("Caught exception while creating archive and sending to SHOCK!")

            if ujs_job_id is not None:
                error_object["status"] = "ERROR : Archive creation failed - {0}".format(e.message)[:handler_utils.UJS_STATUS_MAX]
                error_object["error_message"] = traceback.format_exc()
            
                handler_utils.report_exception(logger, error_object, cleanup_details)

                ujs.complete_job(ujs_job_id, 
                                 kb_token, 
                                 "Download from {0} failed.".format(workspace_name), 
                                 traceback.format_exc(), 
                                 None)
                sys.exit(1)
            else:
                logger.error("Compressing files and saving to SHOCK failed")
                logger.error("Download from {0} failed.".format(workspace_name))
                raise
    
        # Report progress on the overall task being completed
        if ujs_job_id is not None:
            ujs.complete_job(ujs_job_id, 
                             kb_token, 
                             "Download from {0} completed".format(workspace_name), 
                             None, 
                             {"shocknodes" : ["{0}/node/{1}?download_raw".format(shock_service_url,shock_id)], 
                              "shockurl" : shock_service_url, 
                              "results" : [{"server_type" : "Shock", 
                                            "url" : "{0}/node/{1}?download_raw".format(shock_service_url,shock_id), 
                                            "id" : shock_id,
                                            "description": "Download"}]})
        else:
            logger.info("Download from {0} completed".format(workspace_name))
    
        # Almost done, remove the working directory if possible
        if not keep_working_directory:
            handler_utils.cleanup(logger, working_directory)

    except Exception, e:
        if ujs is None or ujs_job_id is None:
            raise

        logger.debug("Caught global exception!")
        
        # handle global exception
        error_object["status"] = "ERROR : {0}".format(e.message)[:handler_utils.UJS_STATUS_MAX]
        error_object["error_message"] = traceback.format_exc()

        handler_utils.report_exception(logger, error_object, cleanup_details)

        ujs.complete_job(ujs_job_id, 
                         kb_token, 
                         "Download from {0} failed.".format(workspace_name), 
                         traceback.format_exc(), 
                         None)
        raise                                  



if __name__ == "__main__":
    logger = script_utils.stderrlogger(__file__, level=logging.DEBUG)
    
    script_details = script_utils.parse_docs(download_taskrunner.__doc__)
        
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
            args.optional_arguments = simplejson.loads(base64.urlsafe_b64decode(args.optional_arguments))
            args.job_details = simplejson.loads(base64.urlsafe_b64decode(args.job_details))
        except Exception, e:
            logger.debug("Exception while loading base64 json strings!")
            sys.exit(1)

    try:
        download_taskrunner(ujs_service_url = args.ujs_service_url,
                            workspace_service_url = args.workspace_service_url,
                            shock_service_url = args.shock_service_url,
                            handle_service_url = args.handle_service_url,
                            fba_service_url = args.fba_service_url,
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
        logger.debug("Download taskrunner threw an exception!")
        logger.exception(e)
        
        ujs = UserAndJobState(url=args.ujs_service_url, token=os.environ.get("KB_AUTH_TOKEN"))
        
        try:
            ujs.complete_job(args.ujs_job_id, 
                             os.environ.get("KB_AUTH_TOKEN"), 
                             "ERROR: {0}".format(e.message)[:handler_utils.UJS_STATUS_MAX], 
                             traceback.format_exc(), 
                             None)
        except Exception, e:
            logger.exception(e)
        
        sys.exit(1)
    
    logger.debug("Download taskrunner completed, exiting normally.")
    sys.exit(0)        
