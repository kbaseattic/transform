
#!/usr/bin/env python

# standard library imports
import os
import sys
import traceback
import argparse
import json
import logging
import io
import pprint
import string

# 3rd party imports
import requests

# KBase imports
import biokbase.Transform.script_utils as script_utils 
import biokbase.workspace.client 


def insert_newlines(string, every):
    lines = []
    for i in xrange(0, len(string), every):
        lines.append(string[i:i+every])
    return '\n'.join(lines)+"\n"

# conversion method that can be called if this module is imported
# Note the logger has different levels it could be run.  See: https://docs.python.org/2/library/logging.html#logging-levels
# The default level is set to INFO which includes everything except DEBUG
def convert(workspace_service_url, shock_service_url, handle_service_url, workspace_name, object_name, object_id, object_version_number, working_directory, level=logging.INFO, logger=None): 
 
    """
    Converts KBaseAssembly.SingleEndLibrary to a Fasta file of assembledDNA.
    Args:
        workspace_service_url :  A url for the KBase Workspace service 
        shock_service_url: A url for the KBase SHOCK service.
        handle_service_url: A url for the KBase Handle Service.
        workspace_name : Name of the workspace
        object_name : Name of the object in the workspace 
        object_version_number : Version number of workspace object (ContigSet), defaults to most recent version
        working_directory : The working directory for where the output file should be stored.
        level: Logging level, defaults to logging.INFO.
    """ 

    if logger is None:
        logger = script_utils.getStderrLogger(__file__)
    
    logger.info("Starting conversion of KBaseGenomes.ContigSet to FASTA.DNA.Assembly")
    token = os.environ.get('KB_AUTH_TOKEN')
    
    if not os.path.isdir(args.working_directory): 
        raise Exception("The working directory does not exist {0} does not exist".format(working_directory)) 

    logger.info("Grabbing Data.")
 
    try:
        ws_client = biokbase.workspace.client.Workspace(workspace_service_url) 
        if object_version_number and object_name :
            contig_set = ws_client.get_objects([{'workspace':workspace_name,'name':object_name, 'ver':object_version_number}])[0] 
        elif object_name:
            contig_set = ws_client.get_objects([{'workspace':workspace_name,'name':object_name}])[0]
        elif object_version_number and object_id :
            contig_set = ws_client.get_objects([{'workspace':workspace_name,'objid':object_id, 'ver':object_version_number}])[0]
        else:
            contig_set = ws_client.get_objects([{'workspace':workspace_name,'objid':object_id}])[0] 
    except Exception, e: 
        logger.exception("Unable to rerieve ws object.")
        logger.exception("".join(traceback.format_exc()))
        raise 

    shock_id = None 
    if "fasta_ref" in contig_set : 
        shock_id  = contig_set['data']['fasta_ref'] 
        logger.info("Retrieving data from Shock.")
        script_utils.download_file_from_shock(logger, shock_service_url, shock_id, working_directory, token) 
        
    else: 
        ws_object_name = contig_set['info'][1]
        valid_chars = "-_.(){0}{1}"format(string.ascii_letters, string.digits)
        output_file_name = ''
        output_file_chars = list()
        for character in ws_object_name:
            if character in valid_chars:
                output_file_chars.append(character)
            else:
                output_file_chars.append('_')
        if len(output_file_chars) == 0:
            output_file_name = "ContigSetFile"
        else:
            output_file_name = ''.join(output_file_chars)

        logger.warning("The ContigSet does not have a fasta_ref to shock.  The fasta file will be attempted to be built from contig sequences in the object.")
        
        output_file =  os.path.join(working_directory,output_file_name)
 
        outFile = open(output_file, 'w') 
        for contig in contig_set['data']['contigs']:
            outFile.write(">{}\n".format(contig['name']))
            #do 80 nucleotides per line
            if contig['sequence'] != '':
                outFile.write(insert_new_lines(contig['sequence'],80))
            else:
                logger.warning("The ContigSet does not have a fasta_ref to shock or sequences in the contigs. A fasta file can not be created.")
                outFile.close()    
                return
        outFile.close()    

    logger.info("Conversion completed.")


# called only if script is run from command line
if __name__ == "__main__":	
    parser = argparse.ArgumentParser(prog='trns_transform_KBaseGenomes_ContigSet_to_FASTA_DNA_Assembly.py', 
                                     description='Converts ContigSet json string into a FASTA file.',
                                     epilog='Authors: Jason Baumohl, Matt Henderson')
    # The following 8 arguments should be fairly standard to all uploaders
    parser.add_argument('--workspace_service_url', help='Workspace service url', action='store', type=str, nargs='?', required=True)
    parser.add_argument('--workspace_name', help ='Workspace Name', action='store', type=str, nargs='?', required=True)
    parser.add_argument('--working_directory', help ='Directory the output file(s) should be written into', action='store', type=str, nargs='?', required=True)
    parser.add_argument('--object_version_number', help ='The version number of the workspace object (ContigSet), defaults to most recent', action='store', type=int, nargs='?', required=False)
 
    object_info = parser.add_mutually_exclusive_group(required=True)
    object_info.add_argument('--object_name', help ='Object Name', action='store', type=str, nargs='?')
    object_info.add_argument('--object_id', help ='Object ID', action='store', type=int, nargs='?') 
 
    data_services = parser.add_mutually_exclusive_group(required=True) 
    data_services.add_argument('--shock_service_url', help='Shock url', action='store', type=str, default='https://kbase.us/services/shock-api/', nargs='?')
    data_services.add_argument('--handle_service_url', help='Handle service url', action='store', type=str, default='https://kbase.us/services/handle_service/', nargs='?')

    args = parser.parse_args()

    logger = script_utils.getStderrLogger(__file__)
    try:
        convert(args.workspace_service_url, args.shock_service_url, args.handle_service_url, args.workspace_name, args.object_name, args.object_id, args.object_version_number, args.working_directory, logger=logger) 
    except:
        logger.exception("".join(traceback.format_exc()))
        print "".join(traceback.format_exc())
        sys.exit(1)
    
    sys.exit(0)

