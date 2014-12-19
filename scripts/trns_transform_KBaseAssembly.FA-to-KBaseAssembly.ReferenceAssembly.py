#!/usr/bin/env python

# standard library imports
import os
import sys
import traceback
import argparse
import json
import logging

# 3rd party imports
import requests

# KBase imports
import biokbase.Transform.script_utils as script_utils


# conversion method that can be called if this module is imported
def convert(shock_url, shock_id, handle_url, handle_id, input_filename, output_filename, level=logging.INFO, logger=None):
    """
    Converts FASTA file to KBaseAssembly.SingleEndLibrary json string.

    Args:
        shock_url: A url for the KBase SHOCK service.
        handle_url: A url for the KBase Handle Service.
        shock_id: A KBase SHOCK node id.
        handle_id: A KBase Handle id.
        input_filename: A file name for the input FASTA data.
        output_filename: A file name where the output JSON string should be stored.
        level: Logging level, defaults to logging.INFO.

    """

    if logger is None:
        logger = script_utils.getStderrLogger(__file__)
    
    logger.info("Starting conversion of FASTA to KBaseAssembly.SingleEndLibrary.")

    token = os.environ.get('KB_AUTH_TOKEN')
    
    logger.info("Gathering information.")
    handles = script_utils.getHandles(logger, shock_url, handle_url, [shock_id], [handle_id],token)   
    
    assert len(handles) != 0
    
    objectString = json.dumps({"handle" : handles[0]}, sort_keys=True, indent=4)
    
    return objectString

# called only if script is run from command line
if __name__ == "__main__":	
    parser = argparse.ArgumentParser(prog='trns_transform_KBaseAssembly.FA-to-KBaseAssembly.SingleEndLibrary', 
                                     description='Converts FASTA file to KBaseAssembly.SingleEndLibrary json string.',
                                     epilog='Authors: Matt Henderson')
    parser.add_argument('-s', '--shock_url', help='Shock url', action='store', type=str, default='https://kbase.us/services/shock-api/', nargs='?')
    parser.add_argument('-n', '--handle_url', help='Handle service url', action='store', type=str, default='https://kbase.us/services/handle_service/', nargs='?')
    parser.add_argument('-f','--input_filename', help ='Input file name', action='store', type=str, nargs='?', required=False)
    parser.add_argument('-o', '--output_filename', help='Output file name', action='store', type=str, nargs='?', required=True)
    parser.add_argument('-r','--reference_name',help='Reference name', action='store', type=str, nargs='?',default=None)

    data_id = parser.add_mutually_exclusive_group(required=True)
    data_id.add_argument('-i', '--shock_id', help='Shock node id', action='store', type=str, nargs='?')
    data_id.add_argument('-d','--handle_id', help ='Handle id', action= 'store', type=str, nargs='?')

    args = parser.parse_args()

    logger = script_utils.getStderrLogger(__file__)
    try:
        ret_json = json.loads(convert(args.shock_url, args.shock_id, args.handle_url, args.handle_id, args.input_filename, args.output_filename,logger=logger))
	if args.reference_name is not None:
		ret_json["reference_name"] = args.reference_name
	logger.info("Writing out JSON.")
    	with open(args.output_filename, "w") as outFile:
        	outFile.write(json.dumps(ret_json,sort_keys = True, indent = 4))
   	logger.info("Conversion completed.")
    except:
        logger.exception("".join(traceback.format_exc()))
        sys.exit(1)
    
    sys.exit(0)
