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
    Converts FASTA file to KBaseAssembly.PairedEndLibrary json string.

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
    
    logger.info("Starting conversion of FASTA to KBaseAssembly.PairedEndLibrary.")

    token = os.environ.get('KB_AUTH_TOKEN')
    
    logger.info("Gathering information.")
    handles = script_utils.getHandles(logger, shock_url, handle_url, shock_id, handle_id,token)   
    
    assert len(handles) != 0
    if len(handles) == 2:    
    	objectString = json.dumps({"handle_1" : handles[0],"handle_2": handles[1]}, sort_keys=True, indent=4)
    else:
	objectString = json.dumps({"handle_1" : handles[0]},sort_keys=True, indent=4)
    
    return objectString

# called only if script is run from command line
if __name__ == "__main__":	
    parser = argparse.ArgumentParser(prog='trns_transform_KBaseAssembly.FA-to-KBaseAssembly.PairedEndLibrary', 
                                     description='Converts FASTA file to KBaseAssembly.PairedEndLibrary json string.',
                                     epilog='Authors: Matt Henderson')
    ret_json = None
    parser.add_argument('-s', '--shock_url', help='Shock url', action='store', type=str, default='https://kbase.us/services/shock-api/', nargs='?')
    parser.add_argument('-n', '--handle_url', help='Handle service url', action='store', type=str, default='https://kbase.us/services/handle_service/', nargs='?')
    parser.add_argument('-f','--input_filenames', help ='PairedEnd Input file names', action='store', type=str, nargs='*', required=False)
    parser.add_argument('-o', '--output_filename', help='Output file name', action='store', type=str, nargs='?', required=True)
    parser.add_argument('-m','--ins_mean', help = 'Mean insert size', action= 'store', dest='ins_mean',type=float,default=None)
    parser.add_argument('-k','--std_dev', help = 'Standard deviation', action= 'store', dest='std_dev',type=float,default=None)
    parser.add_argument('-l','--inl', help = 'Interleaved  -- true/false', action= 'store_true',dest='inl',default=False)
    parser.add_argument('-r','--r_ori', help = 'Read Orientation -- true/false', action= 'store', dest='read_orient',type=int,default=None)

    data_id = parser.add_mutually_exclusive_group(required=True)
    data_id.add_argument('-i', '--shock_ids', help='Paired End Shock node ids (comma seperated)', action='store', type=str, nargs='*')
    data_id.add_argument('-d','--handle_ids', help ='Handle id', action= 'store', type=str, nargs='?')
    
    args = parser.parse_args()

    logger = script_utils.getStderrLogger(__file__)
    #snids = data_id.inobj_id.split(',')
    logger.info("data passed {0}\n{0}\n{0}".format(args.shock_ids,args.handle_ids,args.input_filenames))
    try:
        	
        ret_json =  json.loads(convert(args.shock_url, args.shock_ids, args.handle_url, args.handle_ids, args.input_filenames, args.output_filename,logger=logger))
	if args.ins_mean is not None:
		ret_json["insert_size_mean"] = args.ins_mean
	if args.std_dev is not None:
		ret_json["insert_size_std_dev"] = args.std_dev
	if args.inl:
		ret_json["interleaved"] = 0
	if args.read_orient is not None:
		ret_json["read_orientation_outward"] = args.read_orient
	with open(args.output_filename, "w") as outFile:
        	outFile.write(json.dumps(ret_json,sort_keys=True, indent=4))

        logger.info("Conversion completed.")
             
    except:
        logger.exception("".join(traceback.format_exc()))
        sys.exit(1)
    
    sys.exit(0)

