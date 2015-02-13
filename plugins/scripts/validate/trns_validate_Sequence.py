#!/usr/bin/env python

# standard library imports
import sys
import os
import subprocess
import traceback
import logging
import re

# KBase imports
import biokbase.Transform.script_utils as script_utils


sep_illumina = '/' 
sep_casava_1 = ':Y:' 
sep_casava_2 = ':N:' 

def check_interleavedPE(filename): 
    count  = 0 
    
    infile  = open(filename, 'r') 
    first_line = infile.readline() 
    if sep_illumina in first_line: 
        header1 = re.split('/', first_line)[0] 
    elif sep_casava_1 in first_line or sep_casava_2 in first_line : 
        header1 = re.split('[1,2]:[Y,N]:',first_line)[0] 
    else: 
        header1 = first_line 
    if header1: 
        for line in infile: 
            if re.match(header1,line): 
                count = count + 1 
    infile.close() 
    if count == 1 : 
        stat = 1 
    else: 
        stat = 0 
    return stat 


def validate(input_directory, working_directory, level=logging.INFO, logger=None):
    """
    Validates any file containing sequence data.

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

    checked = False
    validated = True
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
        
        if os.path.splitext(input_file_name)[-1] in fasta_extensions:
            # TODO This needs to be changed, this is really just a demo program for this library and not a serious tool
            java_classpath = os.path.join(os.environ.get("KB_TOP"), "lib/jars/FastaValidator/FastaValidator-1.0.jar")
            arguments = ["java", "-classpath", java_classpath, "FVTester", filePath]

        elif os.path.splitext(input_file_name)[-1] in fastq_extensions:
            line_count = int(subprocess.check_output(["wc", "-l", filePath]).split()[0])
            
            if line_count % 4 > 0:
                #cleans out lines that are empty.  SRA Tool box puts newline on the end.
                #os.system("sed -i '/^$/d' " + filePath)
                cmd_list = ["sed","-i", r"'/^$/d'",filePath]
                filtering = subprocess.Popen(cmd_list, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                stdout, stderr = filtering.communicate()
                if filtering.returncode != 0:
                    raise Exception("sed execution failed for the file {0}".format(filePath))
                
            if (check_interleavedPE(filePath) == 1):
                arguments = ["fastQValidator", "--file", filePath, "--maxErrors", "10", "--disableSeqIDCheck"]      
            else :
                arguments = ["fastQValidator", "--file", filePath, "--maxErrors", "10"] 

        tool_process = subprocess.Popen(arguments, stderr=subprocess.PIPE)
        stdout, stderr = tool_process.communicate()
    
        if tool_process.returncode != 0:
            logger.error("Validation failed on {0}".format(input_file_name))
            validated = False
            break
        else:
            logger.info("Validation passed on {0}".format(input_file_name))
            checked = True
        
    if not validated:
        raise Exception("Validation failed!")
    elif not checked:
        raise Exception("No files were found that had a valid fasta or fastq extension.")
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

