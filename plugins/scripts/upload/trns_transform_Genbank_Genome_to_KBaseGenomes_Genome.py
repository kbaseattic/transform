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
              workspace_name=None, object_name=None, contigset_object_name=None,
              input_directory=None, working_directory=None, 
              level=logging.INFO, logger=None):
    """
    Transforms Genbank file to KBaseGenomes.Genome and KBaseGenomes.ContigSet objects.
    
    Args:
        shock_service_url: If you have shock references you need to make.
        workspace_service_url: KBase Workspace URL
        workspace_name: Name of the workspace to save the data to
        object_name: Name of the genome object to save
        contigset_object_name: Name of the ContigSet object that is created with this Genome
        input_directory: A directory of either a genbank file or a directory of partial genome files to merge
        working_directory: A directory where you can do work
    
    Returns:
        Workspace objects saved to the user's workspace.
    
    Authors:
        Shinjae Yoo, Marcin Joachimiak, Matt Henderson
    """

    if logger is None:
        logger = script_utils.stderrlogger(__file__)
    
    logger.info("Starting transformation of Genbank to KBaseGenomes.Genome")
    
    classpath = ["$KB_TOP/lib/jars/kbase/transform/GenBankTransform.jar",
                 "$KB_TOP/lib/jars/kbase/genomes/kbase-genomes-20140411.jar",
                 "$KB_TOP/lib/jars/kbase/common/kbase-common-0.0.6.jar",
                 "$KB_TOP/lib/jars/jackson/jackson-annotations-2.2.3.jar",
                 "$KB_TOP/lib/jars/jackson/jackson-core-2.2.3.jar",
                 "$KB_TOP/lib/jars/jackson/jackson-databind-2.2.3.jar",
                 "$KB_TOP/lib/jars/kbase/transform/GenBankTransform.jar",
                 "$KB_TOP/lib/jars/kbase/auth/kbase-auth-1398468950-3552bb2.jar",
                 "$KB_TOP/lib/jars/kbase/workspace/WorkspaceClient-0.2.0.jar"]
    
    mc = "us.kbase.genbank.ConvertGBK"

    argslist = ["--shock_url {0}".format(shock_service_url),
                "--workspace_service_url {0}".format(workspace_service_url),
                "--workspace_name {0}".format(workspace_name),
                "--object_name {0}".format(object_name),
                "--working_directory {0}".format(working_directory),
                "--input_directory {0}".format(input_directory)]
    
    if contigset_object_name is not None:
        argslist.append("--contigset_object_name {0}".format(contigset_object_name))

    arguments = ["java", 
                 "-classpath", ":".join(classpath), 
                 "us.kbase.genbank.ConvertGBK", 
                 " ".join(argslist)]

    # need shell in this case because the java code is depending on finding the KBase token in the environment
    tool_process = subprocess.Popen(" ".join(arguments), stderr=subprocess.PIPE, shell=True)
    stdout, stderr = tool_process.communicate()

    if stdout is not None and len(stdout) > 0:
        logger.info(stdout)

    if stderr is not None and len(stderr) > 0:
        logger.error("Transformation from Genbank.Genome to KBaseGenomes.Genome failed on {0}".format(input_directory))
        logger.error(stderr)
        sys.exit(1)
    
    
    logger.info("Transformation from Genbank.Genome to KBaseGenomes.Genome completed.")
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
                        nargs="?", 
                        required=True)
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
    parser.add_argument("--contigset_object_name", 
                        help=script_details["Args"]["contigset_object_name"], 
                        action="store", 
                        type=str, 
                        nargs="?", 
                        required=False)
    parser.add_argument("--input_directory", 
                        help=script_details["Args"]["input_directory"], 
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
    
    args, unknown = parser.parse_known_args()
    
    logger = script_utils.stderrlogger(__file__)
    
    try:
        transform(shock_service_url=args.shock_service_url,
                  workspace_service_url=args.workspace_service_url,
                  workspace_name=args.workspace_name,
                  object_name=args.object_name,
                  contigset_object_name=args.contigset_object_name,
                  input_directory=args.input_directory,
                  working_directory=args.working_directory,
                  logger = logger)
    except Exception, e:
        logger.exception(e)
        sys.exit(1)
    
    sys.exit(0)
