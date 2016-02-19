#!/usr/bin/env python

# standard library imports
import os
import sys
import argparse
import logging
import string
import subprocess

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
    Converts KBaseEnigmaMetals.GrowthMatrix to TSV-formatted file.
    
    Args:
        workspace_service_url:  A url for the KBase Workspace service 
        workspace_name: Name of the workspace
        object_name: Name of the object in the workspace 
        version: Version number of workspace object, defaults to most recent version
        working_directory: The working directory where the output file should be stored.
        output_file_name: The desired file name of the result file.
        level: Logging level, defaults to logging.INFO.
    
    Returns:
        TSV-formatted file containing data from GrowthMatrix object.
    
    Authors:
        Roman Sutormin, Alexey Kazakov
    
    """ 

    if logger is None:
        logger = script_utils.stderrlogger(__file__)
    
    logger.info("Starting conversion of KBaseEnigmaMetals.GrowthMatrix to TSV.Growth")
    token = os.environ.get("KB_AUTH_TOKEN")
    
    if not working_directory or not os.path.isdir(args.working_directory): 
        raise Exception("The working directory {0} does not exist".format(working_directory)) 

    logger.info("Grabbing Data.")

    classpath = ["$KB_TOP/lib/jars/kbase/transform/kbase_transform_deps.jar",
                 "$KB_TOP/lib/jars/apache_commons/commons-cli-1.2.jar",
                 "$KB_TOP/lib/jars/ini4j/ini4j-0.5.2.jar",
                 "$KB_TOP/lib/jars/jackson/jackson-annotations-2.2.3.jar",
                 "$KB_TOP/lib/jars/jackson/jackson-core-2.2.3.jar",
                 "$KB_TOP/lib/jars/jackson/jackson-databind-2.2.3.jar",
                 "$KB_TOP/lib/jars/jetty/jetty-all-7.0.0.jar",
                 "$KB_TOP/lib/jars/jna/jna-3.4.0.jar",
                 "$KB_TOP/lib/jars/kbase/auth/kbase-auth-0.3.1.jar",
                 "$KB_TOP/lib/jars/kbase/common/kbase-common-0.0.10.jar",
                 "$KB_TOP/lib/jars/servlet/servlet-api-2.5.jar",
                 "$KB_TOP/lib/jars/syslog4j/syslog4j-0.9.46.jar",
                 "$KB_TOP/lib/jars/kbase/workspace/WorkspaceClient-0.2.0.jar"]
    
    mc = "us.kbase.kbaseenigmametals.GrowthMatrixDownloader"

    argslist = ["--workspace_service_url {0}".format(workspace_service_url),
                "--workspace_name {0}".format(workspace_name),
                "--object_name {0}".format(object_name),
                "--working_directory {0}".format(working_directory)]

    if output_file_name:
        argslist.append("--output_file_name {0}".format(output_file_name))

    if version:
        argslist.append("--version {0}".format(version))

    arguments = ["java", "-classpath", ":".join(classpath), mc, " ".join(argslist)]

    logger.debug(arguments)

    # need shell in this case because the java code is depending on finding the KBase token in the environment
    tool_process = subprocess.Popen(" ".join(arguments), stderr=subprocess.PIPE, shell=True)
    stdout, stderr = tool_process.communicate()

    if stdout is not None and len(stdout) > 0:
        logger.info(stdout)

    if stderr is not None and len(stderr) > 0:
        logger.error("Transformation from KBaseEnigmaMetals.GrowthMatrix to TSV.Growth failed")
        logger.error(stderr)
        sys.exit(1)
    
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
    logger.info("Starting download of GrowthMatrix => TSV.Growth")
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

