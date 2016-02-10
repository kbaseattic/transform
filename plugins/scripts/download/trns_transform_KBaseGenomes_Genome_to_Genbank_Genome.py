#!/usr/bin/env python

# standard library imports
import sys
import os
import argparse
import logging
import subprocess

# 3rd party imports
# None

# KBase imports
import biokbase.Transform.script_utils as script_utils


def transform(shock_service_url=None, workspace_service_url=None,
              workspace_name=None, object_name=None, object_id=None, object_version=None,
              working_directory=None, output_file_name=None,
              level=logging.INFO, logger=None):
    """
    Transforms KBaseGenomes.Genome and KBaseGenomes.ContigSet objects to Genbank file.
    
    Args:
        shock_service_url: If you have shock references you need to make.
        workspace_service_url: KBase Workspace URL
        workspace_name: Name of the workspace to save the data to
        object_name: Name of the genome object to save
        object_id: Id of the genome object to save
        object_version: Version of the genome object to save
        working_directory: A directory where you can do work
        output_file_name: File name for Genbank output
    
    Returns:
        Genbank output file.
    
    Authors:
        Shinjae Yoo, Matt Henderson, Marcin Joachimiak
    """

    if logger is None:
        logger = script_utils.stderrlogger(__file__)
    
    logger.info("Starting transformation of KBaseGenomes.Genome to Genbank")

    classpath = ["$KB_TOP/lib/jars/kbase/transform/kbase_transform_deps.jar",
                 "$KB_TOP/lib/jars/kbase/genomes/kbase-genomes-20140411.jar",
                 "$KB_TOP/lib/jars/kbase/common/kbase-common-0.0.6.jar",
                 "$KB_TOP/lib/jars/jackson/jackson-annotations-2.2.3.jar",
                 "$KB_TOP/lib/jars/jackson/jackson-core-2.2.3.jar",
                 "$KB_TOP/lib/jars/jackson/jackson-databind-2.2.3.jar",
                 "$KB_TOP/lib/jars/kbase/auth/kbase-auth-1398468950-3552bb2.jar",
                 "$KB_TOP/lib/jars/kbase/workspace/WorkspaceClient-0.2.0.jar"]
    
    argslist = ["--shock_service_url {0}".format(shock_service_url),
                "--workspace_service_url {0}".format(workspace_service_url),
                "--workspace_name {0}".format(workspace_name),
                "--working_directory {0}".format(working_directory)]

    logger.debug(object_name)
    
    if object_id is not None and len(object_id) > 0:
        argslist.append("--object_id {0}".format(object_id))
    elif object_name is not None and len(object_name) > 0:
        object_name_print = object_name.replace("|","\|")
        argslist.append("--object_name {0}".format(object_name_print))
    else:
        logger.error("Transformation from KBaseGenomes.Genome to Genbank.Genome failed due to no object name or id")
        sys.exit(1)   

    if object_version is not None:
        try:
            int(object_version)
        except:
            logger.error("Version number not correct!  Expected integer, but found {0}".format(type(object_version)))
            sys.exit(1)
    
        argslist.append("--object_version {0}".format(object_version))
    
    if output_file_name is not None and len(output_file_name) > 0:
        argslist.append("--output_file {0}".format(output_file_name))

    arguments = ["java", 
                 "-classpath", ":".join(classpath), 
                 "us.kbase.genbank.GenometoGbk", 
                 " ".join(argslist)]

    logger.debug(arguments)

    # need shell in this case because the java code is depending on finding the KBase token in the environment
    tool_process = subprocess.Popen(" ".join(arguments), stderr=subprocess.PIPE, shell=True)
    stdout, stderr = tool_process.communicate()

    if stdout is not None and len(stdout) > 0:
        logger.info(stdout)

    if stderr is not None and len(stderr) > 0:
        logger.error("Transformation from KBaseGenomes.Genome to Genbank.Genome failed on {0}".format(object_name))
        logger.error(stderr)
        sys.exit(1)

    logger.info("Transformation from KBaseGenomes.Genome to Genbank.Genome completed.")
    sys.exit(0)


if __name__ == "__main__":
    script_details = script_utils.parse_docs(transform.__doc__)

    parser = script_utils.ArgumentParser(prog=__file__, 
                                     description=script_details["Description"],
                                     epilog=script_details["Authors"])
    parser.add_argument("--shock_service_url", 
                        help=script_details["Args"]["shock_service_url"], 
                        action="store", 
                       type=str, 
                        nargs='?', 
                        required=False)
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
    #parser.add_argument("--object_id", 
    #                    help=script_details["Args"]["object_id"], 
    #                    action="store", 
    #                    type=int, 
    #                    nargs="?",
    #                    default=None, 
    #                    required=False)
    parser.add_argument("--object_version", 
                        help=script_details["Args"]["object_version"], 
                        action="store", 
                        type=int, 
                        nargs="?", 
                        default=None,
                        required=False)   
    parser.add_argument("--output_file_name",
                        help=script_details["Args"]["output_file_name"],
                        action="store",
                        type=str,
                        nargs="?",
                        required=False)
    parser.add_argument("--working_directory", 
                        help=script_details["Args"]["working_directory"], 
                        action="store", 
                        type=str, 
                        nargs='?', 
                        required=False)
    
    args, unknown = parser.parse_known_args()
    
    logger = script_utils.stderrlogger(__file__, level=logging.DEBUG)
    
    try:
        transform(shock_service_url=args.shock_service_url,
                  workspace_service_url=args.workspace_service_url,
                  workspace_name=args.workspace_name,
                  object_name=args.object_name,
                  object_version=args.object_version,
                  working_directory=args.working_directory,
                  output_file_name=args.output_file_name,
                  logger = logger)
    except Exception, e:
        logger.exception(e)
        sys.exit(1)
    
    sys.exit(0)
