#!/usr/bin/env python

# standard library imports
import os
import sys
import logging
import re
import hashlib

# 3rd party imports
import simplejson

# KBase imports
import biokbase.Transform.script_utils as script_utils


# transformation method that can be called if this module is imported
def transform(shock_service_url=None, handle_service_url=None, 
              output_file_name=None, input_directory=None, 
              working_directory=None, level=logging.INFO, logger=None):
    """
    Converts a FASTQ file to a KBaseAssembly.SingleEndLibrary json string.  

    Args:
        shock_service_url: A url for the KBase SHOCK service.
        handle_service_url: A url for the KBase Handle Service.
        output_file_name: A file name where the output JSON string should be stored.  
        input_directory: The directory containing the file.
        working_directory: The directory the resulting json file will be written to.
        level: Logging level, defaults to logging.INFO.
        
    Returns:
        JSON file on disk that can be saved as a KBase workspace object.

    Authors:
    """

    if logger is None:
        logger = script_utils.stderrlogger(__file__)

    logger.info("Scanning for FASTQ files.")

    valid_extensions = [".fq",".fastq",".fnq"]

    files = os.listdir(working_directory)
    fastq_files = [x for x in files if os.path.splitext(x)[-1] in valid_extensions]
        
    assert len(fastq_files) != 0

    logger.info("Found {0}".format(str(fastq_files)))

    input_file_name = files[0]

    if len(fastq_files) > 1:
        logger.warning("Not sure how to handle multiple FASTQ files in this context. Using {0}".format(input_file_name))


    kb_token = os.environ.get('KB_AUTH_TOKEN')

    script_utils.upload_file_to_shock(logger=logger,
                                      shock_service_url=shock_service_url,
                                      filePath=os.path.join(input_directory, input_file_name),
                                      token=kb_token)

    handles = script_utils.getHandles(logger=logger, 
                                      shock_service_url=shock_service_url, 
                                      handle_service_url=handle_service_url, 
                                      token=kb_token)

    assert len(handles) != 0

    objectString = simplejson.dumps({"handle": handles[0]}, sort_keys=True, indent=4)

    if output_file_name is None:
        output_file_name = input_file_name

    with open(os.path.join(output_directory,output_file_name), "w") as f:
        f.write(objectString)



# called only if script is run from command line
if __name__ == "__main__":
    script_details = script_utils.parse_docs(transform.__doc__)    

    import argparse

    parser = argparse.ArgumentParser(prog=__file__, 
                                     description=script_details["Description"],
                                     epilog=script_details["Authors"])
                                     
    parser.add_argument('--shock_service_url', 
                        help=script_details["Args"]["shock_service_url"],
                        action='store', type=str, nargs='?', required=True)
    parser.add_argument('--handle_service_url', 
                        help=script_details["Args"]["handle_service_url"], 
                        action='store', type=str, nargs='?', default=None, required=False)
    parser.add_argument('--input_directory', 
                        help=script_details["Args"]["input_directory"], 
                        action='store', type=str, nargs='?', required=True)
    parser.add_argument('--working_directory', 
                        help=script_details["Args"]["working_directory"], 
                        action='store', type=str, nargs='?', required=True)
    parser.add_argument('--output_file_name', 
                        help=script_details["Args"]["output_file_name"],
                        action='store', type=str, nargs='?', default=None, required=False)

    parser.add_argument('--input_mapping', 
                        help=script_details["Args"]["input_mapping"], 
                        action='store', type=unicode, nargs='?', default=None, required=False)

    args, unknown = parser.parse_known_args()

    logger = script_utils.stderrlogger(__file__)
    try:
        transform(shock_service_url = args.shock_service_url, 
                  handle_service_url = args.handle_service_url, 
                  output_file_name = args.output_file_name, 
                  input_directory = args.input_directory, 
                  working_directory = args.working_directory, 
                  shock_id = args.shock_id, 
                  handle_id = args.handle_id,
                  logger = logger)
    except Exception, e:
        logger.exception(e)
        sys.exit(1)
    
    sys.exit(0)
