#!/usr/bin/env python

# standard library imports
import sys
import os
import subprocess
import logging
import re

# KBase imports
import biokbase.Transform.script_utils as script_utils

sep_illumina = '/' 
sep_casava_1 = ':Y:' 
sep_casava_2 = ':N:' 

def check_interleavedPE(filename):
    count = 0

    with open(filename, 'r') as infile:
        first_line = infile.readline()
        header1 = None

        if sep_illumina in first_line:
            header1 = first_line.split(sep_illumina)[0]
        elif sep_casava_1 in first_line or sep_casava_2 in first_line:
            header1 = re.split('[1,2]:[Y,N]:',first_line)[0]
        else:
            header1 = first_line

        if header1:
            for line in infile:
                if re.match(header1,line):
                    count = count + 1
        infile.close()

    stat = 0
    if count == 1:
        stat = 1

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
        Srividya Ramikrishnan, Jason Baumohl, Matt Henderson
    """

    if logger is None:
        logger = script_utils.stdoutlogger(__file__, level)

    # TODO get classpaths and binary paths into the config
    KB_TOP = os.environ["KB_TOP"]

    fasta_executable = "{}/lib/jars/FastaValidator/FastaValidator-1.0.jar".format(KB_TOP)
    fastq_executable = "fastQValidator"

    fasta_validator_present = False
    fastq_validator_present = False
    fastq_validator_runnable = False

    if os.path.isfile(fasta_executable):
        fasta_validator_present = True

    for path in os.environ["PATH"].split(os.pathsep):
        path = path.strip('"')
        exe_file = os.path.join(path, fastq_executable)
        if os.path.isfile(exe_file) and os.access(exe_file, os.X_OK):
            fastq_validator_present = True
            fastq_validator_runnable = True
            break
        elif os.path.isfile(exe_file):
            fastq_validator_present = True
            break

    if not fasta_validator_present:
        logger.warning("FASTA validator executable FastaValidator-1.0.jar could not be found.")

    if not fastq_validator_present:
        logger.warning("FASTQ validator executable fastQValidator could not be found.")
    elif not fastq_validator_runnable:
        logger.warning("FASTQ validator executable fastQValidator does not have execute permissions.")

    fasta_extensions = [".fa",".fas",".fasta",".fna"]
    fastq_extensions = [".fq",".fastq",".fnq"]
    
    extensions = fasta_extensions + fastq_extensions

    checked = False
    validated = True
    for input_file_name in os.listdir(input_directory):
        logger.info("Checking for SequenceReads file : {0}".format(input_file_name))

        filePath = os.path.abspath(os.path.join(input_directory, input_file_name))

        if not os.path.isfile(filePath):
            logger.warning("Skipping directory {0}".format(input_file_name))
            continue
        elif os.path.splitext(input_file_name)[-1] not in extensions:
            logger.warning("Unrecognized file type {}, skipping.".format(os.path.splitext(input_file_name)[-1]))
            continue

        logger.info("Starting SequenceReads validation of {0}".format(input_file_name))

        if os.path.splitext(input_file_name)[-1] in fasta_extensions:
            # TODO This needs to be changed, this is really just a demo program for this library and not a serious tool
            arguments = ["java", "-classpath", fasta_executable, "FVTester", "'{}'".format(filePath)]
        elif os.path.splitext(input_file_name)[-1] in fastq_extensions:
            logger.info("Checking FASTQ line count for errors.")
            line_number = 0
            with open(filePath, 'rb') as seqfile:
                for line in seqfile:
                    line_number += 1
            logger.info("FASTQ line count check completed.")

            if line_number % 4 > 0:
                logger.warning("Found extra lines, removing blank lines.")
                out = open(filePath + ".tmp", 'w')
                with open(filePath, 'r') as seqfile:
                    for line in seqfile:
                        if len(line.strip()) == 0:
                            pass
                        out.write(line)
                out.close()
                os.remove(filePath)
                os.rename(filePath + ".tmp", filePath)
                logger.warning("Blank lines removed from FASTQ.")

            arguments = [fastq_executable, "--file", "'{}'".format(filePath), "--maxErrors", "10"]

            if (check_interleavedPE(filePath) == 1):
                arguments.append("--disableSeqIDCheck")

        logger.info("Running {}".format(" ".join(arguments).replace(filePath, input_file_name)))
        tool_process = subprocess.Popen(" ".join(arguments), shell=True)
        tool_process.wait()

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

    returncode = 0

    try:
        validate(input_directory = args.input_directory, 
                 working_directory = args.working_directory)
    except Exception, e:
        logger = script_utils.stderrlogger(__file__, logging.INFO)
        logger.exception(e)
        returncode = 1

    sys.stdout.flush()
    sys.stderr.flush()
    os.close(sys.stdout.fileno())
    os.close(sys.stderr.fileno())    
    sys.exit(returncode)

