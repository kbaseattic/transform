#!/usr/bin/env python

# standard library imports
import os
import sys
import argparse
import logging
import string

try:
    import cStringIO as StringIO
except:
    import StringIO

# 3rd party imports
# None

# KBase imports
import biokbase.Transform.script_utils as script_utils 

from doekbase.data_api.sequence.assembly.api import AssemblyAPI
from doekbase.data_api.core import ObjectAPI
from doekbase.handle.Client import AbstractHandle as handleClient

#services = {"workspace_service_url": "https://ci.kbase.us/services/ws/",
#            "shock_service_url": "https://ci.kbase.us/services/shock-api/",
#            "handle_service_url": "https://ci.kbase.us/services/handle_service/"}


# Download method that can be called if this module is imported
# Note the logger has different levels with which it could be run.  See: https://docs.python.org/2/library/logging.html#logging-levels
# The default level is set to INFO which includes everything except DEBUG
def transform(workspace_service_url=None, shock_service_url=None, handle_service_url=None, 
              workspace_name=None, object_name=None, object_id=None, 
              object_version_number=None, working_directory=None, output_file_name=None, 
              level=logging.INFO, logger=None):  
    """
    Converts KBaseGenomeAnnotations.Assembly to FASTA.
    
    Args:
        workspace_service_url:  A url for the KBase Workspace service 
        shock_service_url: A url for the KBase SHOCK service.
        handle_service_url: A url for the KBase Handle Service.
        workspace_name: Name of the workspace
        object_name: Name of the Assembly object in the workspace 
        object_id: Id of the Assembly object in the workspace, mutually exclusive to object_name
        object_version_number: Version number of workspace object (Assembly), defaults to most recent version
        working_directory: The working directory where the output file should be stored.
        output_file_name: The desired file name of the resulting FASTA file.
        level: Logging level, defaults to logging.INFO.
    
    Returns:
        A FASTA file containing header and sequence data from an Assembly object.
    
    Authors:
        Marcin Joachimiak
    
    """ 


    if logger is None:
        logger = script_utils.stdoutlogger(__file__)
    
    logger.info("Starting conversion of KBaseGenomeAnnotations.Assembly to Fasta")
    token = os.environ.get("KB_AUTH_TOKEN")
    
    if not os.path.isdir(args.working_directory): 
        raise Exception("The working directory does not exist {0} does not exist".format(working_directory)) 

    logger.info("Grabbing Data.")
 
    services = {"workspace_service_url": workspace_service_url, 
    "shock_service_url": "https://ci.kbase.us/services/shock-api/",
    "handle_service_url": handle_service_url}

    assembly_ref = workspace_name+"/"+object_name
    try:

        asm_api = AssemblyAPI(services, token=token, ref=assembly_ref)

    except Exception, e: 
        logger.exception("Unable to create AssemblyAPI {0}:{1}:{2}.".format(workspace_service_url,workspace_name, assembly_ref))
        logger.exception(e)
        raise 

    #shock_id = None 
    #build_up_object = False
    #if "fasta_ref" in contig_set["data"]: 
    #    shock_id = contig_set["data"]["fasta_ref"] 
    #    logger.info("Trying to Retrieve data from Shock.")
    #    try:
    #        script_utils.download_file_from_shock(logger = logger, 
    #                                              shock_service_url = shock_service_url, 
    #                                              shock_id = shock_id, 
    #                                              directory = working_directory, 
    #                                              token = token)
    #    except Exception, e:
    #        logger.warning("Unable to retrive the contig set from shock.  Trying to build from the object")
    #        build_up_object = True 
    #else: 
    #    build_up_object = True
        
    #contig_ids = asm_api.get_contig_ids()
    #print ",".join(contig_ids)

    #contigs = asm_api.get_contigs(contig_ids)
    #print contigs[contig_ids[0]]

    #output = StringIO.StringIO()
    #asm_api.get_fasta().to_file(output)

    #if(output_file_name.endswith(".fa") or output_file_name.endswith(".fasta") or output_file_name.endswith(".fna")):
    #    blah=1
    #else:
    #    output_file_name= '{}.fasta'.format(output_file_name)

    if output_file_name is None:
        output_file_name = object_name + ".fasta"

    with open(output_file_name, 'w') as outFile:
        asm_api.get_fasta().to_file(outFile)

    logger.info("Conversion completed.")


# called only if script is run from command line
if __name__ == "__main__":
    script_details = script_utils.parse_docs(transform.__doc__)

    parser = argparse.ArgumentParser(prog=__file__, 
                                     description=script_details["Description"],
                                     epilog=script_details["Authors"])
    
    # The following 8 arguments should be fairly standard to all uploaders
    parser.add_argument("--workspace_service_url", 
                        help=script_details["Args"]["workspace_service_url"], 
                        action="store", 
                        type=str, 
                        nargs="?", 
                        required=True)
    parser.add_argument("--workspace_name", 
                        help=script_details["Args"]["workspace_name"], 
                        action="store", 
                        type=str, 
                        nargs="?", 
                        required=True)
    parser.add_argument("--working_directory", 
                        help=script_details["Args"]["working_directory"], 
                        action="store", 
                        type=str, 
                        nargs="?", 
                        required=True)

    parser.add_argument("--output_file_name", 
                        help=script_details["Args"]["output_file_name"], 
                        action="store", 
                        type=str, 
                        nargs="?", 
                        required=False)
    parser.add_argument("--object_version_number", 
                        help=script_details["Args"]["object_version_number"], 
                        action="store", 
                        type=int, 
                        nargs="?", 
                        required=False)

    object_info = parser.add_mutually_exclusive_group(required=True)
    object_info.add_argument("--object_name", 
                             help=script_details["Args"]["object_name"], 
                             action="store", 
                             type=str, 
                             nargs="?") 
    object_info.add_argument("--object_id", 
                             help=script_details["Args"]["object_id"], 
                             action="store", 
                             type=int, 
                             nargs="?")

    data_services = parser.add_mutually_exclusive_group(required=True) 
    data_services.add_argument("--shock_service_url", 
                        help=script_details["Args"]["shock_service_url"], 
                        action="store", 
                        type=str, 
                        nargs="?") 
    data_services.add_argument("--handle_service_url", 
                        help=script_details["Args"]["handle_service_url"], 
                        action="store", 
                        type=str, 
                        nargs="?")

    args = parser.parse_args()

    logger = script_utils.stderrlogger(__file__)
    logger.info("Starting download of Assembly => FASTA")
    try:
        transform(workspace_service_url = args.workspace_service_url, 
                  shock_service_url = args.shock_service_url, 
                  handle_service_url = args.handle_service_url, 
                  workspace_name = args.workspace_name, 
                  object_name = args.object_name, 
                  object_id = args.object_id, 
                  object_version_number = args.object_version_number, 
                  output_file_name = args.output_file_name,
                  working_directory = args.working_directory, 
                  logger = logger)
    except Exception, e:
        logger.exception(e)
        sys.exit(1)
    
    sys.exit(0)

