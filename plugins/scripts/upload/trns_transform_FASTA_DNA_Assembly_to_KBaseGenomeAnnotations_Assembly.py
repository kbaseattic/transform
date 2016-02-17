#!/usr/bin/env python

# standard library imports
import os
import sys
import logging
import re
import hashlib
import time 
import traceback 
import os.path 
import datetime
import collections
from string import digits

# 3rd party imports
import simplejson

# KBase imports
import biokbase.Transform.script_utils as script_utils
import biokbase.Transform.TextFileDecoder as TextFileDecoder
import biokbase.workspace.client 

# transformation method that can be called if this module is imported
# Note the logger has different levels it could be run.  
# See: https://docs.python.org/2/library/logging.html#logging-levels
#
# The default level is set to INFO which includes everything except DEBUG
#@profile
def upload_assembly(shock_service_url = None, 
                    handle_service_url = None,
                    input_directory = None,
#                    shock_id = None,
#                  handle_id = None,
                    input_mapping = None,
                    workspace_name = None, 
                    workspace_service_url = None, 
                    taxon_reference = None, 
                    assembly_name = None, 
                    source = None, 
                    date_string = None,
                    contig_information_dict = None,
                    logger = None):

    """
    Uploads CondensedGenomeAssembly
    Args:
        shock_service_url: A url for the KBase SHOCK service.
        handle_service_url: A url for the KBase Handle service.
        shock_id: If the shock id exists use same file (NEEDS TO BE UPDATED TO HANDLE ID)
        input_mapping: (not sure, I think for mapping multiple files, not needed here only 1 file expected)
        workspace_name: Name of ws to load into
        workspace_service_url: URL of WS server instance the WS is on.
        taxon_reference: The ws reference the assembly points to.  (Optional)
        assembly_name: Name of the assembly object to be created. (Optional) (defaults to file_name)
        source: The source of the data (Ex: Refseq)
        date_string: Date (or date range) associated with data. (Optional)
        contig_information_dict: A mapping that has is_circular and description information (Optional)
        
    Returns:
        JSON file on disk that can be saved as a KBase workspace object.
    Authors:
        Jason Baumohl, Matt Henderson
    """
    if logger is None:
        logger = script_utils.stderrlogger(__file__)

    logger.info("Starting conversion of FASTA to Assembly object")
    token = os.environ.get('KB_AUTH_TOKEN')
 
    if input_mapping is None: 
        logger.info("Scanning for FASTA files.")
 
        valid_extensions = [".fa",".fasta",".fna",".fas"] 
 
#        files = os.listdir(input_directory)
        files = os.listdir(os.path.abspath(input_directory))
        fasta_files = [x for x in files if os.path.splitext(x)[-1] in valid_extensions]
 
        if (len(fasta_files) == 0): 
            raise Exception("The input file does not have one of the following extensions .fa, .fasta, .fas or .fna") 
 
 
        logger.info("Found {0}".format(str(fasta_files))) 
 
        fasta_file_name = os.path.join(input_directory,fasta_files[0]) 
 
        if len(fasta_files) > 1: 
            logger.warning("Not sure how to handle multiple FASTA files in this context. Using {0}".format(fasta_file_name)) 
    else: 
        logger.info("Input Mapping not none : " + str(input_mapping))
        fasta_file_name = os.path.join(os.path.join(input_directory, "FASTA.DNA.Assembly"), simplejson.loads(input_mapping)["FASTA.DNA.Assembly"]) 
 
    logger.info("Building Object.") 
 
    if not os.path.isfile(fasta_file_name): 
        raise Exception("The fasta file name {0} is not a file!".format(fasta_file_name)) 
                    
    if not os.path.isdir(input_directory): 
        raise Exception("The input directory {0} is not a valid directory!".format(input_directory)) 

    ws_client = biokbase.workspace.client.Workspace(workspace_service_url)
 
    workspace_object = ws_client.get_workspace_info({'workspace':workspace_name}) 

    workspace_id = workspace_object[0] 
    workspace_name = workspace_object[1] 
    
    print "FASTA FILE Name :"+ fasta_file_name + ":"

    if assembly_name is None:
        base = os.path.basename(fasta_file_name) 
        assembly_name = "{0}_assembly".format(os.path.splitext(base)[0])


    ##########################################
    #ASSEMBLY CREATION PORTION  - consume Fasta File
    ##########################################

    logger.info("Starting conversion of FASTA to Assemblies")
    logger.info("Building Assembly Object.")

    input_file_handle = TextFileDecoder.open_textdecoder(fasta_file_name, 'ISO-8859-1')    
    fasta_header = None
    fasta_description = None
    sequence_list = []
    fasta_dict = dict()
    first_header_found = False
    contig_set_md5_list = []
    # Pattern for replacing white space
    pattern = re.compile(r'\s+')
    sequence_exists = False
    
    total_length = 0
    gc_length = 0
    #Note added X and x due to kb|g.1886.fasta
    valid_chars = "-AaCcGgTtUuWwSsMmKkRrYyBbDdHhVvNnXx"
    amino_acid_specific_characters = "PpLlIiFfQqEe" 

    sequence_start = 0
    sequence_stop = 0

    current_line = input_file_handle.readline()
    while current_line != None and len(current_line) > 0:
#        print "CURRENT LINE: " + current_line
        if (current_line[0] == ">"):
            # found a header line
            # Wrap up previous fasta sequence
            if (not sequence_exists) and first_header_found:
                logger.error("There is no sequence related to FASTA record : {0}".format(fasta_header))        
                raise Exception("There is no sequence related to FASTA record : {0}".format(fasta_header))
            if not first_header_found:
                first_header_found = True
                sequence_start = 0
            else:
                sequence_stop = input_file_handle.tell() - len(current_line)
                # build up sequence and remove all white space
                total_sequence = ''.join(sequence_list)
                total_sequence = re.sub(pattern, '', total_sequence)
                if not total_sequence :
                    logger.error("There is no sequence related to FASTA record : {0}".format(fasta_header)) 
                    raise Exception("There is no sequence related to FASTA record : {0}".format(fasta_header))
#                for character in total_sequence:
#                    if character not in valid_chars:
#                        if character in amino_acid_specific_characters:
#                            raise Exception("This fasta file may have amino acids in it instead of the required nucleotides.")
#                        raise Exception("This FASTA file has non nucleic acid characters : {0}".format(character))
                seq_count = collections.Counter(total_sequence)
                seq_dict = dict(seq_count)
                for character in seq_dict:
                    if character not in valid_chars:
                        if character in amino_acid_specific_characters:
                            raise Exception("This fasta file may have amino acids in it instead of the required nucleotides.")
                        raise Exception("This FASTA file has non nucleic acid characters : {0}".format(character))
                length = len(total_sequence)
                total_length = total_length + length
                contig_gc_length = len(re.findall('G|g|C|c',total_sequence))
                contig_dict = dict() 
                contig_dict["gc_content"] = float(contig_gc_length)/float(length) 
                gc_length = gc_length + contig_gc_length
                fasta_key = fasta_header.strip()
                contig_dict["contig_id"] = fasta_key 
                contig_dict["length"] = length 
                contig_dict["name"] = fasta_key 
                contig_md5 = hashlib.md5(total_sequence.upper()).hexdigest() 
                contig_dict["md5"] = contig_md5 
                contig_set_md5_list.append(contig_md5)

                contig_dict["is_circular"] = "Unknown"
                if fasta_description is not None: 
                    contig_dict["description"] = fasta_description
                if contig_information_dict is not None:
                    if contig_information_dict[fasta_key] is not None:
                        if contig_information_dict[fasta_key]["definition"] is not None:
                            contig_dict["description"] = contig_information_dict[fasta_key]["definition"]
                        if contig_information_dict[fasta_key]["is_circular"] is not None:
                            contig_dict["is_circular"] = contig_information_dict[fasta_key]["is_circular"]
                contig_dict["start_position"] = sequence_start
                contig_dict["num_bytes"] = sequence_stop - sequence_start

#                print "Sequence Start: " + str(sequence_start) + "Fasta: " + fasta_key
#                print "Sequence Stop: " + str(sequence_stop) + "Fasta: " + fasta_key

                if fasta_key in fasta_dict:
                    raise Exception("The fasta header {0} appears more than once in the file ".format(fasta_key))
                else: 
                    fasta_dict[fasta_key] = contig_dict
               
                # get set up for next fasta sequence
                sequence_list = []
                sequence_exists = False
                
#               sequence_start = input_file_handle.tell()               
            sequence_start = 0            

            fasta_header_line = current_line.strip().replace('>','')
            try:
                fasta_header , fasta_description = fasta_header_line.split(' ',1)
            except:
                fasta_header = fasta_header_line
                fasta_description = None
        else:
            if sequence_start == 0:
                sequence_start = input_file_handle.tell() - len(current_line) 
            sequence_list.append(current_line)
            sequence_exists = True
        current_line = input_file_handle.readline()
#        print "ENDING CURRENT LINE: " + current_line

    # wrap up last fasta sequence
    if (not sequence_exists) and first_header_found: 
        logger.error("There is no sequence related to FASTA record : {0}".format(fasta_header))        
        raise Exception("There is no sequence related to FASTA record : {0}".format(fasta_header)) 
    elif not first_header_found :
        logger.error("There are no contigs in this file") 
        raise Exception("There are no contigs in this file") 
    else: 
        sequence_stop = input_file_handle.tell()
        # build up sequence and remove all white space      
        total_sequence = ''.join(sequence_list)
        total_sequence = re.sub(pattern, '', total_sequence)
        if not total_sequence :
            logger.error("There is no sequence related to FASTA record : {0}".format(fasta_header)) 
            raise Exception("There is no sequence related to FASTA record : {0}".format(fasta_header)) 

#        for character in total_sequence: 
        seq_count = collections.Counter(total_sequence) 
        seq_dict = dict(seq_count) 
        for character in seq_dict: 
            if character not in valid_chars: 
                if character in amino_acid_specific_characters:
                    raise Exception("This fasta file may have amino acids in it instead of the required nucleotides.")
                raise Exception("This FASTA file has non nucleic acid characters : {0}".format(character))

        length = len(total_sequence)
        total_length = total_length + length
        contig_gc_length = len(re.findall('G|g|C|c',total_sequence))
        contig_dict = dict()
        contig_dict["gc_content"] = float(contig_gc_length)/float(length) 
        gc_length = gc_length + contig_gc_length
        fasta_key = fasta_header.strip()
        contig_dict["contig_id"] = fasta_key 
        contig_dict["length"] = length
        contig_dict["name"] = fasta_key

        contig_dict["is_circular"] = "Unknown"
        if fasta_description is not None:
            contig_dict["description"] = fasta_description
        if contig_information_dict is not None: 
            if contig_information_dict[fasta_key] is not None:
                if contig_information_dict[fasta_key]["definition"] is not None:
                    contig_dict["description"] = contig_information_dict[fasta_key]["definition"]
                if contig_information_dict[fasta_key]["is_circular"] is not None:
                    contig_dict["is_circular"] = contig_information_dict[fasta_key]["is_circular"]
        contig_md5 = hashlib.md5(total_sequence.upper()).hexdigest()
        contig_dict["md5"]= contig_md5
        contig_set_md5_list.append(contig_md5)
        contig_dict["start_position"] = sequence_start
        contig_dict["num_bytes"] = sequence_stop - sequence_start
        
        if fasta_key in fasta_dict:
            raise Exception("The fasta header {0} appears more than once in the file ".format(fasta_key))
        else: 
            fasta_dict[fasta_key] = contig_dict
        input_file_handle.close()

    contig_set_dict = dict()
    contig_set_dict["md5"] = hashlib.md5(",".join(sorted(contig_set_md5_list))).hexdigest()
    contig_set_dict["assembly_id"] = assembly_name
    contig_set_dict["name"] = assembly_name
    contig_set_dict["external_source"] = source
    contig_set_dict["external_source_id"] = os.path.basename(fasta_file_name) 
#    contig_set_dict["external_source_origination_date"] = str(os.stat(fasta_file_name).st_ctime)

    if date_string is not None:
        contig_set_dict["external_source_origination_date"] = date_string
    contig_set_dict["contigs"] = fasta_dict
    contig_set_dict["dna_size"] = total_length
    contig_set_dict["gc_content"] = float(gc_length)/float(total_length)
#    print "Fasta dict Keys :"+",".join(fasta_dict.keys())+":" 
    contig_set_dict["num_contigs"] = len(fasta_dict.keys())
    contig_set_dict["type"] = "Unknown"
    contig_set_dict["notes"] = "Note MD5s are generated from uppercasing the sequences" 
    if taxon_reference is not None:
        contig_set_dict["taxon_ref"] = taxon_reference


    shock_id = None
    handle_id = None
    if shock_id is None:
        shock_info = script_utils.upload_file_to_shock(logger, shock_service_url, fasta_file_name, token=token)
        shock_id = shock_info["id"]
        handles = script_utils.getHandles(logger, shock_service_url, handle_service_url, [shock_id], [handle_id], token)   
        handle_id = handles[0]

    contig_set_dict["fasta_handle_ref"] = handle_id

    # For future development if the type is updated to the handle_reference instead of a shock_reference
    assembly_not_saved = True 
    assembly_provenance = [{"script": __file__, "script_ver": "0.1", "description": "Generated from fasta files generated from v5 of the CS."}]
    while assembly_not_saved: 
        try: 
            assembly_info =  ws_client.save_objects({"workspace": workspace_name,"objects":[ 
                {"type":"KBaseGenomeAnnotations.Assembly", 
                 "data":contig_set_dict, 
                 "name": assembly_name, 
                 "provenance":assembly_provenance}]}) 
            assembly_not_saved = False 
        except biokbase.workspace.client.ServerError as err: 
            print "ASSEMBLY SAVE FAILED ON genome " + str(assembly_name) + " ERROR: " + str(err) 
            raise 
        except: 
            print "ASSEMBLY SAVE FAILED ON genome " + str(assembly_name) + " GENERAL_EXCEPTION: " + str(sys.exc_info()[0]) 
            raise 
    
    logger.info("Conversion completed.")


# called only if script is run from command line
if __name__ == "__main__":
    script_details = script_utils.parse_docs(upload_assembly.__doc__)    

    import argparse

    parser = argparse.ArgumentParser(prog=__file__, 
                                     description=script_details["Description"],
                                     epilog=script_details["Authors"])
                                     
    parser.add_argument('--shock_service_url', 
                        help=script_details["Args"]["shock_service_url"],
                        action='store', type=str, nargs='?', required=True)
    parser.add_argument('--handle_service_url', 
                        help=script_details["Args"]["handle_service_url"], 
                        action='store', type=str, nargs='?', default=None, required=True)
    parser.add_argument('--workspace_name', nargs='?', help='workspace name to populate', required=True)
    parser.add_argument('--workspace_service_url', action='store', type=str, nargs='?', required=True) 
    parser.add_argument('--taxon_reference', nargs='?', help='The ws object reference for the related taxon.  If not set the taxon reference will not get set in the object', required=False)

    parser.add_argument('--object_name', 
                        help="name of object to create.  If not specified it defaults to the file name.", 
                        nargs='?', required=False) 
    parser.add_argument('--source', 
                        help="data source : examples Refseq, Genbank, Pythozyme, Gramene, etc", 
                        nargs='?', required=False, default="User upload") 
    parser.add_argument('--input_directory', 
                        help="Directory the fasta file is in", 
                        action='store', type=str, nargs='?', required=True)
#    parser.add_argument('--shock_id', 
#                        help=script_details["Args"]["shock_id"],
#                        action='store', type=str, nargs='?', default=None, required=False)
#    parser.add_argument('--handle_id', 
#                        help=script_details["Args"]["handle_id"], 
#                        action='store', type=str, nargs='?', default=None, required=False)

#    parser.add_argument('--input_mapping', 
#                        help=script_details["Args"]["input_mapping"], 
#                        action='store', type=unicode, nargs='?', default=None, required=False)

    args, unknown = parser.parse_known_args()

    logger = script_utils.stderrlogger(__file__)

    logger.debug(args)
    try:
    
        upload_assembly(shock_service_url = args.shock_service_url, 
                        handle_service_url = args.handle_service_url, 
                        input_directory = args.input_directory, 
#                  shock_id = args.shock_id, 
#                  handle_id = args.handle_id,
#                  input_mapping = args.input_mapping,
                        workspace_name = args.workspace_name,
                        workspace_service_url = args.workspace_service_url,
                        taxon_reference = args.taxon_reference,
                        assembly_name = args.object_name,
                        source = args.source,
                        logger = logger)
    except Exception, e:
        logger.exception(e)
        sys.exit(1)
    
    sys.exit(0)


