#!/usr/bin/env python

# standard library imports
import sys
import os
import argparse
import logging

# 3rd party imports
# None

# KBase imports
import biokbase.Transform.script_utils as script_utils


def transform(shock_service_url=None, handle_service_url=None,               
              working_directory=None, level=logging.INFO, logger=None)
    """
    Transforms Genbank file to KBaseGenomes.Genome and KBaseGenomes.ContigSet objects.
    
    Args:
        shock_service_url: If you have shock references you need to make.
        handle_service_url: In case your type has at least one handle reference.
        working_directory: A directory where you can do work.
    
    Returns:
        JSON representing a KBase object.
    
    Authors:
        Shinjae Yoo, Matt Henderson
    
    """

    if logger is None:
        logger = script_utils.stderrlogger(__file__)
    
    logger.info("Starting transformation of Genbank to KBaseGenomes.Genome")
    
    token = os.environ.get("KB_AUTH_TOKEN")

    classpath = "$KB_TOP/lib/jars/kbase/genomes/kbase-genomes-20140411.jar:$KB_TOP/lib/jars/kbase/common/kbase-common-0.0.6.jar:$KB_TOP/lib/jars/jackson/jackson-annotations-2.2.3.jar:$KB_TOP/lib/jars/jackson/jackson-core-2.2.3.jar:$KB_TOP/lib/jars/jackson/jackson-databind-2.2.3.jar:$KB_TOP/lib/jars/kbase/transform/GenBankTransform.jar:$KB_TOP/lib/jars/kbase/auth/kbase-auth-1398468950-3552bb2.jar:$KB_TOP/lib/jars/kbase/workspace/WorkspaceClient-0.2.0.jar"
    mc = 'us.kbase.genbank.ConvertGBK'

    java_classpath = os.path.join(os.environ.get("KB_TOP"), classpath.replace('$KB_TOP', kb_top))
    arguments = ["java", "-classpath", java_classpath, "us.kbase.genbank.ConvertGBK", working_directory]
        
    tool_process = subprocess.Popen(arguments, stderr=subprocess.PIPE)
    stdout, stderr = tool_process.communicate()

    if len(stderr) > 0:
        logger.error("Validation failed on {0}".format(input_file_name))
    else:
        logger.info("Validation passed on {0}".format(input_file_name))
        validated = True

    input_directory = os.path.dirname(os.path.abspath(args.input_file_directory))
    
    logger.info("Transform completed.")


if __name__ == "__main__":
    script_details.parse_docs(transform.__doc__)

    parser = argparse.ArgumentParser(prog=__file__, 
                                     description=script_details["Description"],
                                     epilog=script_details["Authors"])
    parser.add_argument("--shock_service_url", 
                        help=script_details["Args"]["shock_service_url"], 
                        action="store", 
                        type=str, 
                        nargs='?', 
                        required=False)
    parser.add_argument("--handle_service_url", 
                        help=script_details["Args"]["handle_service_url"], 
                        action="store", 
                        type=str, 
                        nargs="?", 
                        required=False)
    parser.add_argument("--input_file_name", 
                        help=script_details["Args"]["input_file_name"], 
                        action="store", 
                        type=str, 
                        nargs='?', 
                        required=True)
    parser.add_argument("--working_directory", 
                        help=script_details["Args"]["working_directory"], 
                        action="store", 
                        type=str, 
                        nargs='?', 
                        required=True)
    
    args, unknown = args.parse_known_args()
    
    logger = script_utils.stderrlogger(__file__)
    
    try:
        transform(shock_service_url=args.shock_service_url,
                  handle_service_url=args.handle_service_url,
                  working_directory=args.working_directory,
                  logger = logger)
    except Exception, e:
        logger.exception(e)
        sys.exit(1)
    
    sys.exit(0)
