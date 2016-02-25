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


def transform(input_file=None,
              level=logging.INFO, logger=None):
    """
    Validate Genbank file.
    
    Args:
        input_directory: An genbank input file
    
    Returns:
        Any validation errors or success.
    
    Authors:
        Shinjae Yoo, Matt Henderson, Marcin Joachimiak
    """

    if logger is None:
        logger = script_utils.stderrlogger(__file__)
    
    logger.info("Starting Genbank validation")
    
    token = os.environ.get("KB_AUTH_TOKEN")

    classpath = "/kb/dev_container/modules/transform/lib/jars/kbase/transform/kbase_transform_deps.jar:$KB_TOP/lib/jars/kbase/genomes/kbase-genomes-20140411.jar:$KB_TOP/lib/jars/kbase/common/kbase-common-0.0.6.jar:$KB_TOP/lib/jars/jackson/jackson-annotations-2.2.3.jar:$KB_TOP/lib/jars/jackson/jackson-core-2.2.3.jar:$KB_TOP/lib/jars/jackson/jackson-databind-2.2.3.jar:$KB_TOP/lib/jars/kbase/transform/kbase_transform_deps.jar:$KB_TOP/lib/jars/kbase/auth/kbase-auth-1398468950-3552bb2.jar:$KB_TOP/lib/jars/kbase/workspace/WorkspaceClient-0.2.0.jar"
    mc = 'us.kbase.genbank.ValidateGBK'

    java_classpath = os.path.join(os.environ.get("KB_TOP"), classpath.replace('$KB_TOP', os.environ.get("KB_TOP")))
    
    argslist = "{0}".format("--input_file {0}".format(input_file))
    
    arguments = ["java", "-classpath", java_classpath, "us.kbase.genbank.ConvertGBK", argslist]

    print arguments        
    tool_process = subprocess.Popen(arguments, stderr=subprocess.PIPE)
    stdout, stderr = tool_process.communicate()

    if len(stderr) > 0:
        logger.error("Validation of Genbank.Genome failed on {0}".format(input_file))
        sys.exit(1)
    else:
        logger.info("Validation of Genbank.Genome completed.")
        sys.exit(0)


if __name__ == "__main__":
    script_details = script_utils.parse_docs(transform.__doc__)

    parser = argparse.ArgumentParser(prog=__file__, 
                                     description=script_details["Description"],
                                     epilog=script_details["Authors"])
    parser.add_argument("--input_file", 
                        help=script_details["Args"]["input_file"], 
                        action="store", 
                        type=str, 
                        nargs='?', 
                        required=True)
    
    args, unknown = parser.parse_known_args()
    
    logger = script_utils.stderrlogger(__file__)
    
    try:
        transform(input_file=args.input_file,
                  logger = logger)
    except Exception, e:
        logger.exception(e)
        sys.exit(1)
    
    sys.exit(0)
