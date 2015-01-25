#!/usr/bin/env python

# standard library imports
import sys
import os
import subprocess
import traceback
import logging

# KBase imports
import biokbase.Transform.script_utils as script_utils


def validate(input_directory, working_directory, level=logging.INFO, logger=None):
    """
    Validates a FASTA file of nucleotide sequences.

    Args:
        input_directory: A directory containing one or more SequenceRead files.
        working_directory: A directory where any output files produced by validation can be written.
        level: Logging level, defaults to logging.INFO.
    
    Returns:
        Currently writes to stderr with a Java Exception trace on error, otherwise no output.
    
    Authors:
        Srividya Ramikrishnan, Matt Henderson
    """

    if logger is None:
        logger = script_utils.stderrlogger(__file__)

    fasta_extensions = [".fa",".fasta",".fna"]
    fastq_extensions = [".fq",".fastq",".fnq"]
        
    extensions = fasta_extensions + fastq_extensions
    
    validated = False
    for input_file_name in os.listdir(input_directory):
        logger.info("Checking for SequenceReads file : {0}".format(input_file_name))

        filePath = os.path.join(os.path.abspath(input_directory), input_file_name)
        
        if not os.path.isfile(filePath):
            logger.warning("Skipping directory {0}".format(input_file_name))
            continue
        elif os.path.splitext(input_file_name)[-1] not in extensions:
            logger.warning("Unrecognized file type, skipping.")
            continue
    
        logger.info("Starting SequenceReads validation of {0}".format(input_file_name))
        
        # TODO This needs to be changed, this is really just a demo program for this library and not a serious tool
        java_classpath = os.path.join(os.environ.get("KB_TOP"), "lib/jars/FastaValidator/FastaValidator-1.0.jar")
        arguments = ["java", "-classpath", java_classpath, "FVTester", filePath]
            
        tool_process = subprocess.Popen(arguments, stderr=subprocess.PIPE)
        stdout, stderr = tool_process.communicate()
    
        if len(stderr) > 0:
            logger.error("Validation failed on {0}".format(input_file_name))
        else:
            logger.info("Validation passed on {0}".format(input_file_name))
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
    parser.add_argument("--input_directory", help=script_details["Args"]["input_directory"], type=str, nargs="?", required=True)
    parser.add_argument("--working_directory", help=script_details["Args"]["working_directory"], type=str, nargs="?", required=True)

    args, unknown = parser.parse_known_args()

    logger = script_utils.stderrlogger(__file__)
    
    try:
        validate(input_directory = args.input_directory, 
                 working_directory = args.working_directory,
                 level = logging.DEBUG,
                 logger = logger)
    except Exception, e:
        logger.exception(e)
        sys.exit(1)
    
    sys.exit(0)

