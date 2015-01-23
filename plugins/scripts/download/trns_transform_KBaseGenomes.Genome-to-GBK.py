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
              working_directory=None, output_file=None,
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
        output_file: File name for Genbank output
    
    Returns:
        Genbank output file.
    
    Authors:
        Shinjae Yoo, Matt Henderson, Marcin Joachimiak
    """

    if logger is None:
        logger = script_utils.stderrlogger(__file__)
    
    logger.info("Starting transformation of KBaseGenomes.Genome to Genbank")
    
    token = os.environ.get("KB_AUTH_TOKEN")

    classpath = "/kb/dev_container/modules/transform/lib/jars/kbase/transform/GenBankTransform.jar:$KB_TOP/lib/jars/kbase/genomes/kbase-genomes-20140411.jar:$KB_TOP/lib/jars/kbase/common/kbase-common-0.0.6.jar:$KB_TOP/lib/jars/jackson/jackson-annotations-2.2.3.jar:$KB_TOP/lib/jars/jackson/jackson-core-2.2.3.jar:$KB_TOP/lib/jars/jackson/jackson-databind-2.2.3.jar:$KB_TOP/lib/jars/kbase/transform/GenBankTransform.jar:$KB_TOP/lib/jars/kbase/auth/kbase-auth-1398468950-3552bb2.jar:$KB_TOP/lib/jars/kbase/workspace/WorkspaceClient-0.2.0.jar"
    mc = 'us.kbase.genbank.ConvertGBK'

    java_classpath = os.path.join(os.environ.get("KB_TOP"), classpath.replace('$KB_TOP', os.environ.get("KB_TOP")))
    
    argslist = "{0} {1} {2} {3} {4} {5}".format("--workspace_service_url {0}".format(workspace_service_url),
                                                      "--workspace_name {0}".format(workspace_name),                                                     
                                                      "--working_directory {0}".format(working_directory))
    #"--shock_service_url {0}".format(shock_service_url),
    if object_name is not None:
        argslist = "{0} {1}".format(arglist, "--object_name {0}".format(object_name))
    elif object_id is not None:
         argslist = "{0} {1}".format(arglist, "--object_id {0}".format(object_id))
    else:
        logger.error("Transformation from KBaseGenomes.Genome to Genbank.Genome failed due to no object name or id")
        sys.exit(1)   
    if object_version is not None:
        argslist = "{0} {1}".format(arglist, "--object_version {0}".format(object_version))

    arguments = ["java", "-classpath", java_classpath, "us.kbase.genbank.GenometoGbk", argslist]

    print arguments        
    tool_process = subprocess.Popen(arguments, stderr=subprocess.PIPE)
    stdout, stderr = tool_process.communicate()

    if len(stderr) > 0:
        logger.error("Transformation from KBaseGenomes.Genome to Genbank.Genome failed on {0}".format(input_directory))
        sys.exit(1)
    else:
        logger.info("Transformation from KBaseGenomes.Genome to Genbank.Genome completed.")
        sys.exit(0)


if __name__ == "__main__":
    script_details = script_utils.parse_docs(transform.__doc__)

    parser = argparse.ArgumentParser(prog=__file__, 
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
    parser.add_argument("--object_id", 
                        help=script_details["Args"]["object_id"], 
                        action="store", 
                        type=str, 
                        nargs="?", 
                        required=False)
    parser.add_argument("--object_version", 
                        help=script_details["Args"]["object_version"], 
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
    
    logger = script_utils.stderrlogger(__file__)
    
    try:
        transform(shock_service_url=args.shock_service_url,
                  workspace_service_url=args.workspace_service_url,
                  workspace_name=args.workspace_name,
                  object_name=args.object_name,
                  object_id=args.object_name,
                  object_version=args.object_name,
                  working_directory=args.working_directory,
                  logger = logger)
    except Exception, e:
        logger.exception(e)
        sys.exit(1)
    
    sys.exit(0)
