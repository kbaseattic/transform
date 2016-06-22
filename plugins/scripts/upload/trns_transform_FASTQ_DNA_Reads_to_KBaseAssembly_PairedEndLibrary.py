#!/usr/bin/env python

# standard library imports
import os
import sys
import traceback
import argparse
import json
import logging
# 3rd party imports
# None

# KBase imports
import biokbase.Transform.script_utils as script_utils
import subprocess
import os.path


# conversion method that can be called if this module is imported
def transform( shock_service_url, handle_service_url, input_directory, 
               working_directory, output_file_name,
               object_name, mean_insert, std_dev, interleaved, read_orientation,
               sra,
#level=logging.INFO, 
             logger=None
           ):
    """
    Converts FASTQ file to KBaseAssembly.PairedEndLibrary json string.

    Args:
        shock_service_url: A url for the KBase SHOCK service.
        handle_service_url: A url for the KBase Handle Service.
        input_directory: Where the FASTQ file can be found.
        working_directory: The directory the resulting json file will be written to.
        output_file_name: A file name where the output JSON string should be stored.  
        object_name: A name to use when storing the JSON string.
        mean_insert: The average insert size.
        std_dev: standard deviation of the inserts
        interleaved: Are the reads interleaved?
        read_orientation: Do the reads have an outward orientation?
        sra:  int flag indicating whether or not to preconvert SRA file into FASTQ
        level: Logging level, defaults to logging.INFO.

    Returns:
        Something

    Authors:
    """

    if logger is None:
        logger = script_utils.stderrlogger(__file__)
    
    logger.info("Starting conversion of FASTQ to KBaseAssembly.PairedEndLibrary.")

    token = os.environ.get('KB_AUTH_TOKEN')

    if  sra > 0 :
        if  not os.path.isfile( "fastq-dump" ) :
            logger.error( "did not find fastq-dump in working directory" )
            raise Exception( "did not find fastq-dump in working directory" )

        if  not os.access( "fastq-dump", os.X_OK ) :
            logger.error( "fastq-dump is not executable" )
            raise Exception( "fastq-dump is not executable" )

        logger.info( "scanning for SRA files" )

        files = os.listdir(working_directory)
        sra_files = [x for x in files if os.path.splitext(x)[-1] in [".sra"]]

        if  len( sra_files ) < 1 :
            logger.error( "no sra files found in working directory" )
            raise Exception( "no sra files found in working directory" )

        if  len( sra_files ) > 1 :
            logger.error( "several sra files found in working directory, exiting" )
            raise Exception( "several sra files found in working directory, exiting" )

        logger.info( "converting " + sra_files[0] + " to fastq" )
        subprocess.check_call( [ "./fastq-dump", "--split-files", sra_files[0] ] )

    # scan the directory for files
    logger.info("Scanning for FASTQ files.")
    
    valid_extensions = [".fq",".fastq",".fnq"]
    
    files = os.listdir(working_directory)
    fastq_files = [x for x in files if os.path.splitext(x)[-1] in valid_extensions]
            
    assert len(fastq_files) != 0
    
    # put the files in shock, get handles
    shock_ids = list()
    #for x in fastq_files:
    for input_file_name in fastq_files:
        shock_info = script_utils.upload_file_to_shock(logger, shock_service_url, input_file_name, token=token)
        shock_ids.append(shock_info["id"])
    
    logger.info("Gathering information.")
    #handles = script_utils.getHandles(logger, shock_service_url, handle_service_url, shock_ids, [handle_id], token)   
    handles = script_utils.getHandles( logger, shock_service_url, handle_service_url, shock_ids, token=token)   
    
    assert len(handles) != 0

    # fill out the object details
    resultObject = dict()
    resultObject["handle_1"] = handles[0]
    
    if len(handles) == 2:
        resultObject["handle_2"] = handles[1]

    if mean_insert is not None :
    	resultObject["insert_size_mean"] = mean_insert
    
    if std_dev is not None:
    	resultObject["insert_size_std_dev"] = std_dev

    if interleaved:    
        resultObject["interleaved"] = 1
    
    if read_orientation:
    	resultObject["read_orientation_outward"] = 1

    objectString = json.dumps(resultObject, sort_keys=True, indent=4)
    
    logger.info("Writing out JSON.")
    if output_file_name is None :
        output_file_name = "default_output_name"
    
    with open( output_file_name, "w" ) as outFile:
        outFile.write(objectString)
    
    logger.info("Conversion completed.")


# called only if script is run from command line
if __name__ == "__main__":
    #script_details = script_utils.parse_docs(transform.__doc__)
    script_details = script_utils.parse_docs(transform.__doc__)

    parser = argparse.ArgumentParser(prog=__file__, 
                                     description=script_details["Description"],
                                     epilog=script_details["Authors"])
    parser.add_argument('--shock_service_url', 
                        help=script_details["Args"]["shock_service_url"], 
                        action='store', 
                        type=str, 
                        nargs='?',
                        required=True)
    parser.add_argument('--handle_service_url', 
                        help=script_details["Args"]["handle_service_url"], 
                        action='store', 
                        type=str, 
                        nargs='?',
                        required=True)
    parser.add_argument('--input_directory', 
                        help=script_details["Args"]["input_directory"], 
                        action='store', 
                        type=str, 
                        nargs='?', 
                        required=False)
    parser.add_argument('--working_directory', 
                        help=script_details["Args"]["working_directory"], 
                        action='store', 
                        type=str, 
                        nargs='?', 
                        required=True),
    parser.add_argument('--output_file_name', 
                        help=script_details["Args"]["output_file_name"],
                        action='store', type=str, nargs='?', default=None, required=False)
    parser.add_argument('--object_name', 
                        help=script_details["Args"]["object_name"], 
                        action='store', 
                        type=str, 
                        nargs='?', 
                        required=True)
    parser.add_argument('--mean_insert', 
                        help= 'Mean insert size', 
                        action='store', 
                        type=float,
                        default=None)
    parser.add_argument('--std_dev', 
                        help='Standard deviation', 
                        action='store', 
                        type=float, 
                        default=None)
    parser.add_argument('--sra', 
                        help='convert SRA to FASTQ beforehand', 
                        action='store', 
                        type=int, 
                        default=0)
    parser.add_argument('--interleaved', 
                        help=script_details["Args"]["interleaved"], 
                        action='store_true')
    parser.add_argument('--read_orientation', 
                        help=script_details["Args"]["read_orientation"], 
                        action='store')

    args, unknown = parser.parse_known_args()


    logger = script_utils.stderrlogger(__file__)

    try:
        transform(shock_service_url = args.shock_service_url, 
                  handle_service_url = args.handle_service_url, 
                  input_directory = args.input_directory, 
                  working_directory = args.working_directory, 
                  output_file_name = args.output_file_name,
                  object_name = args.object_name,
                  mean_insert = args.mean_insert,
                  std_dev = args.std_dev,
                  interleaved = args.interleaved,
                  read_orientation = args.read_orientation,
                  sra = args.sra,
                  logger = logger)
    except Exception, e:
        logger.exception(e)
        sys.exit(1)
    
    sys.exit(0)

