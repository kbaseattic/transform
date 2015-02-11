#!/usr/bin/env python

# standard library imports
import sys
import os
import subprocess
import traceback
import logging

# KBase imports
import biokbase.Transform.script_utils as script_utils


def validate(input_file_name, working_directory, level=logging.INFO, logger=None):
    """
    Validates any file containing sequence data.

    Args:
        input_file_name: An input SBML file.
        working_directory: A directory where any output files produced by validation can be written.
        level: Logging level, defaults to logging.INFO.
    
    Returns:
        0 on success, 1 on failure.
        All statements passed to standard out via a logger, any errors throw an Exception
        and result in a non-zero exit status back to the caller.
    
    Authors:
        Srividya Ramikrishnan, Matt Henderson
    """

    if logger is None:
        logger = script_utils.stdoutlogger(__file__)

    command = os.path.join(os.environ.get("KB_TOP"), "bin/validateSBML")
    
    validated = False
    fileName = os.path.split(input_file_name)[-1]
        
    if not os.path.isfile(input_file_name):
        raise Exception("Not a file {0}".format(fileName))

    logger.info("Starting SBML validation of {0}".format(fileName))
    
    arguments = [command, input_file_name]        
        
    tool_process = subprocess.Popen(arguments, stderr=subprocess.PIPE)
    stdout, stderr = tool_process.communicate()

    if len(stderr) > 0:
        logger.error("Validation failed on {0}".format(fileName))
    else:
        logger.info("Validation passed on {0}".format(fileName))
        validated = True
        
    if not validated:
        raise Exception("Validation failed!")
    else:
        logger.info("Validation passed.")


if __name__ == "__main__":
    script_details = script_utils.parse_docs(validate.__doc__)

    import argparse

    parser = argparse.ArgumentParser(prog=__file__,
                                     description=script_details["Description"],                                     
                                     epilog=script_details["Authors"])
    parser.add_argument("--input_file_name", help=script_details["Args"]["input_file_name"], type=str, nargs="?", required=True)
    parser.add_argument("--working_directory", help=script_details["Args"]["working_directory"], type=str, nargs="?", required=True)

    args = parser.parse_args()

    logger = script_utils.stdoutlogger(__file__)
    
    try:
        validate(input_file_name = args.input_file_name, 
                 working_directory = args.working_directory,
                 level = logging.DEBUG,
                 logger = logger)
    except Exception, e:
        logger.exception(e)
        sys.exit(1)
    
    sys.exit(0)
