#!/usr/bin/env python

# standard library imports
import os
import sys
import argparse
import logging
import string

# 3rd party imports
# None

# KBase imports
import biokbase.Transform.script_utils as script_utils 
import biokbase.workspace.client 


# conversion method that can be called if this module is imported
# Note the logger has different levels it could be run.  See: https://docs.python.org/2/library/logging.html#logging-levels
# The default level is set to INFO which includes everything except DEBUG
def transform(workspace_service_url=None, workspace_name=None, object_name=None,
              version=None, working_directory=None, output_file_name=None, 
              level=logging.INFO, logger=None):  
    """
    Converts KBaseFeatureValues.ExpressionMatrix to TSV-formatted file.
    
    Args:
        workspace_service_url:  A url for the KBase Workspace service 
        workspace_name: Name of the workspace
        object_name: Name of the object in the workspace 
        version: Version number of workspace object, defaults to most recent version
        working_directory: The working directory where the output file should be stored.
        output_file_name: The desired file name of the result file.
        level: Logging level, defaults to logging.INFO.
    
    Returns:
        TSV-formatted file containing data from ExpressionMatrix object.
    
    Authors:
        Roman Sutormin
    
    """ 

    if logger is None:
        logger = script_utils.stderrlogger(__file__)
    
    logger.info("Starting conversion of KBaseFeatureValues.ExpressionMatrix to TSV")
    token = os.environ.get("KB_AUTH_TOKEN")
    
    if not os.path.isdir(args.working_directory): 
        raise Exception("The working directory does not exist {0} does not exist".format(working_directory)) 

    logger.info("Grabbing Data.")
 
    if not output_file_name:
        output_file_name = "test.tsv"
    output_file = os.path.join(working_directory, output_file_name)

    with open(output_file, "w") as outFile:
        outFile.write("feature_ids\tfirst_condition\ntmp0001\t3.0\n")
    
    logger.info("Conversion completed.")


# called only if script is run from command line
if __name__ == "__main__":
    script_details = script_utils.parse_docs(transform.__doc__)

    parser = argparse.ArgumentParser(prog=__file__, 
                                     description=script_details["Description"],
                                     epilog=script_details["Authors"])
    
    # The following 8 arguments should be fairly standard to all uploaders
    parser.add_argument("--workspace_service_url", 
                        help=script_details["Args"]["workspace_service_url"], 
                        action="store", 
                        type=str, 
                        nargs="?", 
                        required=True)
    parser.add_argument("--workspace_name", 
                        help=script_details["Args"]["workspace_name"], 
                        action="store", 
                        type=str, 
                        nargs="?", 
                        required=True)

    parser.add_argument("--object_name", 
                        help=script_details["Args"]["object_name"], 
                        action="store", 
                        type=str, 
                        nargs="?",
                        required=True) 

    parser.add_argument("--working_directory", 
                        help=script_details["Args"]["working_directory"], 
                        action="store", 
                        type=str, 
                        nargs="?", 
                        required=True)

    parser.add_argument("--output_file_name", 
                        help=script_details["Args"]["output_file_name"], 
                        action="store", 
                        type=str, 
                        nargs="?", 
                        required=False)

    parser.add_argument("--version", 
                        help=script_details["Args"]["version"], 
                        action="store", 
                        type=int, 
                        nargs="?", 
                        required=False)

    args = parser.parse_args()

    logger = script_utils.stderrlogger(__file__)
    logger.info("Starting download of ExpressionMatrix => TSV")
    try:
        transform(workspace_service_url = args.workspace_service_url, 
                  workspace_name = args.workspace_name, 
                  object_name = args.object_name, 
                  version = args.version, 
                  output_file_name = args.output_file_name,
                  working_directory = args.working_directory, 
                  logger = logger)
    except Exception, e:
        logger.exception(e)
        sys.exit(1)
    
    sys.exit(0)

