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


def main():
    """
    KBase Convert task manager for converting between KBase objects.
    
    Step 1 - Run a converter to pull the source object and save the destination object.
    
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
        source_workspace_name: The name of the source workspace.
        destination_workspace_name: The name of the destination workspace.
        source_object_name: The source object name.
        destination_object_name: The destination object name.
        source_object_id: A source object id, which can be used instead of object_name.
        destination_object_id: A destination object id, which can be used instead of 
                               object_name.
        source_kbase_type: The KBase Workspace type string that indicates the module
                           and type of the object being created.                       
        destination_kbase_type: The KBase Workspace type string that indicates the module
                                and type of the object being created.
        optional_arguments: This is a JSON string containing optional parameters that can
                            be passed in for custom behavior per conversion.
        ujs_job_id: The job id from the User and Job State service that can be used to
                    report status on task progress back to the user.
        job_details: This is a JSON string that passes in the script specific command
                     line options for a given conversion type.  The service pulls
                     these config settings from a script config created by the developer
                     of the conversion script and passes that into the AWE job that
                     calls this script.
        working_directory: The working directory on disk where files can be created and
                           will be cleaned when the job ends with success or failure.
        keep_working_directory: A flag to tell the script not to delete the working
                                directory, which is mainly for debugging purposes.
    
    Returns:
        Literal return value is 0 for success and 1 for failure.
        
        Actual data output is one or more Workspace objects saved to a user's workspace. 
        
    Authors:
        Matt Henderson, Gavin Price            
    """

    logger = script_utils.stderrlogger(__file__)
    logger.info("Executing KBase Convert tasks")
    
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
    parser.add_argument('--source_workspace_name', 
                        help=script_details["Args"]["source_workspace_name"], 
                        action='store', 
                        required=True)
    parser.add_argument('--source_object_name', 
                        help=script_details["Args"]["source_object_name"], 
                        action='store', 
                        required=True)
    parser.add_argument('--source_object_id', 
                        help=script_details["Args"]["source_object_id"], 
                        action='store')


    # workspace info for saving the data
    parser.add_argument('--destination_workspace_name', 
                        help=script_details["Args"]["destination_workspace_name"], 
                        action='store', 
                        required=True)
    parser.add_argument('--destination_object_name', 
                        help=script_details["Args"]["destination_object_name"], 
                        action='store', 
                        required=True)
    parser.add_argument('--destination_object_id', 
                        help=script_details["Args"]["destination_object_id"], 
                        action='store')

    # the types that we are transforming between, currently assumed one to one 
    parser.add_argument('--source_kbase_type', 
                        help=script_details["Args"]["source_kbase_type"], 
                        action='store', 
                        required=True)
    parser.add_argument('--destination_kbase_type', 
                        help=script_details["Args"]["destination_kbase_type"], 
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

    # ignore any extra arguments
    args, unknown = parser.parse_known_args()
            
    kb_token = os.environ.get('KB_AUTH_TOKEN')
    ujs = UserAndJobState(url=args.ujs_service_url, token=kb_token)

    est = datetime.datetime.utcnow() + datetime.timedelta(minutes=3)
    if args.ujs_job_id is not None:
        ujs.update_job_progress(args.ujs_job_id, kb_token, "KBase Data Convert started", 
                                1, est.strftime('%Y-%m-%dT%H:%M:%S+0000'))

    # parse all the json strings from the argument list into dicts
    # TODO had issues with json.loads and unicode strings, workaround was using simplejson and base64
    
    args.optional_arguments = simplejson.loads(base64.urlsafe_b64decode(args.optional_arguments))
    args.job_details = simplejson.loads(base64.urlsafe_b64decode(args.job_details))
    
    if not os.path.exists(args.working_directory):
        os.mkdir(args.working_directory)

    if args.ujs_job_id is not None:
        ujs.update_job_progress(args.ujs_job_id, kb_token, 
                                "Converting from {0} to {1}".format(args.source_kbase_type,args.destination_kbase_type), 
                                1, est.strftime('%Y-%m-%dT%H:%M:%S+0000') )

    # Step 1 : Convert the objects
    try:
        convert_args = args.job_details["convert"]
        convert_args["optional_arguments"] = args.optional_arguments
        convert_args["working_directory"] = args.working_directory
        
        handler_utils.run_task(logger, validation_args)
    except Exception, e:
        handler_utils.report_exception(logger, 
                         {"message": 'ERROR : Conversion from {0} to {1}'.format(args.source_kbase_type,args.destination_kbase_type),
                          "exc": e,
                          "ujs": ujs,
                          "ujs_job_id": args.ujs_job_id,
                          "token": kb_token,
                         },
                         {"keep_working_directory": args.keep_working_directory,
                          "working_directory": args.working_directory})

        ujs.complete_job(args.ujs_job_id, 
                         kb_token, 
                         "Convert to {0} failed.".format(args.destination_workspace_name), 
                         e, 
                         None)                                  

    
    # Report progress on the overall task being completed
    if args.ujs_job_id is not None:
        ujs.complete_job(args.ujs_job_id, 
                         kb_token, 
                         "Convert to {0} completed".format(args.destination_workspace_name), 
                         None, 
                         {"shocknodes" : [], 
                          "shockurl" : args.shock_service_url, 
                          "workspaceids" : [], 
                          "workspaceurl" : args.workspace_service_url,
                          "results" : None})
    
    # Almost done, remove the working directory if possible
    if not args.keep_working_directory:
        handler_utils.cleanup(logger, args.working_directory)

    sys.exit(0);

if __name__ == "__main__":
    main()    