#!/usr/bin/env python

import argparse
import sys
import os
import datetime
import traceback
import shutil
import json

from biokbase.workspace.client import Workspace
from biokbase import log
from biokbase.userandjobstate.client import UserAndJobState
from biokbase.Transform.ProcessHandler import upload_handler


if __name__ == "__main__":
    # Parse options.
    parser = argparse.ArgumentParser(description="Upload Handler for converting from external data formats to KBase objects")
    parser.add_argument('--workspace_service_url', help='Workspace url', action='store', default='https://kbase.us/services/ws/', required=True)
    parser.add_argument('--ujs_service_url', help='UJS url', action='store', default='https://kbase.us/services/userandjobstate/', required=True)
    parser.add_argument('--shock_service_url', help='Shock url', action='store', default='https://kbase.us/services/shock-api/')
    parser.add_argument('--handle_service_url', help='Handle service url', action='store', default='https://kbase.us/services/handle_service/')

    # service method inputs
    parser.add_argument('--url', help='Data URL', action='store', required=True)
    parser.add_argument('--workspace_name', help='Destination workspace name', action='store', required=True)
    parser.add_argument('--object_name', help='Output workspace object name', action='store', required=True)
    parser.add_argument('--object_id', help='Output workspace object id', action='store')
    parser.add_argument('--external_type', help='External object type', action='store', required=True)
    parser.add_argument('--kbase_type', help='KBase object type', action='store', required=True)
    parser.add_argument('--optional_arguments', help='Optional arguments json string', action='store', default='{}')

    parser.add_argument('--ujs_job_id', help='UJS job id', action='store', default=None, required=False)
    parser.add_argument('--job_details', help='Info needed to run the upload job', action='store', default=None)

    parser.add_argument('--working_directory', help='Working directory', action='store', default=None, required=True)
    parser.add_argument('--keep_working_directory', help='Keep working directory on completion if a new directory was created', action='store_true')
    parser.add_argument('--input_temporary_file', help='Input temporary file name', action='store', default='infile')
    parser.add_argument('--output_temporary_file', help='Output temporary file name', action='store', default='outfile')

    args = parser.parse_args()
    
    kb_token = os.environ.get('KB_AUTH_TOKEN')
    ujs = UserAndJobState(url=args.ujs_service_url, token=kb_token)

    est = datetime.datetime.utcnow() + datetime.timedelta(minutes=3)
    if args.ujs_job_id is not None:
        ujs.update_job_progress(args.ujs_job_id, kb_token, 'Dispatched', 1, est.strftime('%Y-%m-%dT%H:%M:%S+0000') )

    ## main loop
    #print >> sys.stderr, args.job_details
    #print >> sys.stderr, args.optional_arguments

    args.job_details = json.loads(args.job_details.replace("\\", ""))
    
    args.optional_arguments = json.loads(args.optional_arguments.replace("\\", ""))
    if 'uploader' not in args.optional_arguments:
        args.optional_arguments['uploader'] = {}
        args.optional_arguments['uploader']['file'] = args.output_temporary_file
        args.optional_arguments['uploader']['input'] = args.url
        args.optional_arguments['uploader']['ujs_job_id'] = args.ujs_job_id
        args.optional_arguments['uploader']['external_type'] = args.external_type
    uploader = Uploader(args)

    try:
        uploader.download_from_urls()
    except:
        if args.ujs_job_id is not None:
            e,v,t = sys.exc_info()[:3]
            ujs.complete_job(args.ujs_job_id, kb_token, 'Failed : data download from \n'.format(args.url), str(v), {}) 
        else:
            traceback.print_exc(file=sys.stderr)
        sys.exit(3);

    if args.ujs_job_id is not None:
        ujs.update_job_progress(args.ujs_job_id, kb_token, 'Data downloaded', 1, est.strftime('%Y-%m-%dT%H:%M:%S+0000') )

    try:
        uploader.validation_handler()
    except:
        if args.ujs_job_id is not None:
            e,v = sys.exc_info()[:2]
            ujs.complete_job(args.ujs_job_id, kb_token, 'Failed : data validation\n', str(v), {}) 
        else:
            traceback.print_exc(file=sys.stderr)
        sys.exit(4);

    if args.ujs_job_id is not None:
        ujs.update_job_progress(args.ujs_job_id, kb_token, 'Data validated', 1, est.strftime('%Y-%m-%dT%H:%M:%S+0000') )

    try:
        uploader.transformation_handler()
    except:
        e,v = sys.exc_info()[:2]
        if args.ujs_job_id is not None:
            ujs.complete_job(args.ujs_job_id, kb_token, 'Failed : data format conversion\n{0}:{1}'.format(str(e),str(v)), {}, {})
        else:
            traceback.print_exc(file=sys.stderr)
            print >> sys.stderr, 'Failed : data format conversion\n{}:{}'.format(str(e),str(v))
        sys.exit(5);

    if args.ujs_job_id is not None:
        ujs.update_job_progress(args.ujs_job_id, kb_token, 'Data format conversion', 1, est.strftime('%Y-%m-%dT%H:%M:%S+0000') )

    try:
        uploader.upload_handler()
    except:
        e,v = sys.exc_info()[:2]
        if args.ujs_job_id is not None:
            ujs.complete_job(args.ujs_job_id, kb_token, 'Failed : upload to WS ({}/{})\n'.format(args.ws_id, args.outobj_id), str(v), {})
        else:
            traceback.print_exc(file=sys.stderr)
            print >> sys.stderr, 'Failed : upload to WS ({}/{})\n{}:{}'.format(args.ws_id, args.outobj_id, str(e),str(v))
        sys.exit(6);

    # clean-up
    if not args.keep_working_directory:
        try:
            shutil.rmtree("{}".format(args.working_directory))
        except:
            logger.error("Unable to remove working directory {0}".format(args.working_directory))

    if args.ujs_job_id is not None:
        ujs.complete_job(args.ujs_job_id, kb_token, 'Success', None, 
                         {"shocknodes" : [], 
                          "shockurl" : args.shock_service_url, 
                          "workspaceids" : [], 
                          "workspaceurl" : args.workspace_service_url,
                          "results" : [{"server_type" : "Workspace", 
                                        "url" : args.workspace_service_url, 
                                        "id" : "{}/{}".format(args.workspace_name, args.object_name), "description" : "description"}]})
    sys.exit(0);
