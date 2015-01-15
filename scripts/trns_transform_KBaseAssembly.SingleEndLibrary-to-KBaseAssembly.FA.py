#!/usr/bin/env python

# standard library imports
import os
import sys
import traceback
import argparse
import json
import logging
import hashlib
# 3rd party imports
import requests

# KBase imports
import biokbase.Transform.script_utils as script_utils
from biokbase.workspace.client import Workspace as workspaceService
from biokbase.shock import Client as shockService

#token = os.environ['KB_AUTH_TOKEN']
def _get_shock_data(token,shock_url,nodeid, binary=False):
    shock = shockService(shock_url, token)
    return shock.download_to_string(nodeid, binary=binary)

def _get_ws(token,workspace_url,wsname, name, wtype):
    ws = workspaceService(workspace_url) 
    #logger.info("token is {}, workspace_url is {} , workspace_name {} , object_name {} , object_type {}".format(token,workspace_url,wsname,name,wtype))
    obj = ws.get_object({'auth': token, 'workspace': wsname, 'id': name, 'type': wtype})
    #logger.info("obj {}".format(json.dumps(obj)))
    data = None
    # Data format
    if 'data' in obj:
        data = obj['data']
    return data

# conversion method that can be called if this module is imported
def convert(workspace_url, shock_url, handle_url, workspace_name, object_name, object_type, output_filename, level=logging.INFO, logger=None):
    """
    Converts KBaseAssembly.SingleEndLibrary to a fasta file.

    Args:
	workspace_url :  A url for the KBase Workspace service
        shock_url: A url for the KBase SHOCK service.
        handle_url: A url for the KBase Handle Service.
        workspace_name : Name of the workspace
        obj_name : Name of the object
        output_filename: A file name where the output JSON string should be stored.
        level: Logging level, defaults to logging.INFO.

    """
    md5 = None 
    if logger is None:
        logger = script_utils.getStderrLogger(__file__)
    
    logger.info("Starting conversion of FASTA to KBaseAssembly.SingleEndLibrary.")

    token = os.environ.get('KB_AUTH_TOKEN')
    
    logger.info("Gathering information.")
    ws_object=_get_ws(token,workspace_url,workspace_name,object_name,object_type)
    
    if "handle" in ws_object and "id" in ws_object['handle']:
	shock_id  = ws_object['handle']['id']
    if "handle" in ws_object and  "remote_md5" in ws_object['handle']:
	md5 = ws_object['handle']['remote_md5']    	
    
    objectString = _get_shock_data(token,shock_url,shock_id)	
    #handles = script_utils.getHandles(logger, shock_url, handle_url, [shock_id], [handle_id], token)   
    
    #assert len(handles) != 0
    hasher = hashlib.md5()     
    #objectString = json.dumps(ws_object, sort_keys=True, indent=4)
    

    logger.info("Writing out Fasta file.")
    with open(args.output_filename, "w") as outFile:
        outFile.write(objectString)
    if md5 is not None:
    	with open(args.output_filename, "rb") as afile:
		buf = afile.read()
		hasher.update(buf)
     
    	fmd5 = hasher.hexdigest()
    	logger.info("fmd5 is {}, md5 is {}".format(fmd5,md5))
    	assert md5 == fmd5

    logger.info("Conversion completed.")


# called only if script is run from command line
if __name__ == "__main__":	
    parser = argparse.ArgumentParser(prog='trns_transform_KBaseAssembly.SingleEndLibrary-to-KBaseAssembly.FA', 
                                     description='Converts SingleEndLibrary file to fasta file',
                                     epilog='Authors: Srividya Ramakrishnan')
    parser.add_argument('-w', '--workspace_url', help='Workspace service url', action='store', type=str, default='http://kbase.us/services/ws', nargs='?')
    parser.add_argument('-s', '--shock_url', help='Shock url', action='store', type=str, default='https://kbase.us/services/shock-api/', nargs='?')
    parser.add_argument('-n', '--handle_url', help='Handle service url', action='store', type=str, default='https://kbase.us/services/handle_service/', nargs='?')
    parser.add_argument('-k','--workspace_name', help ='Workspace Name', action='store', type=str, nargs='?', required=False)
    parser.add_argument('-f','--object_name', help ='Object Name', action='store', type=str, nargs='?', required=False)
    parser.add_argument('-o', '--output_filename', help='Output file name', action='store', type=str, nargs='?', required=True)

    #data_id = parser.add_mutually_exclusive_group(required=True)
    #data_id.add_argument('-i', '--shock_id', help='Shock node id', action='store', type=str, nargs='?')
    #data_id.add_argument('-d','--handle_id', help ='Handle id', action= 'store', type=str, nargs='?')

    args = parser.parse_args()

    logger = script_utils.getStderrLogger(__file__)
    object_type = 'KBaseAssembly.SingleEndLibrary'
    try:
        convert(args.workspace_url,args.shock_url, args.handle_url,args.workspace_name,args.object_name,object_type,args.output_filename, logger=logger)
    except:
        logger.exception("".join(traceback.format_exc()))
        sys.exit(1)
    
    sys.exit(0)

