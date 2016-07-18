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
import shutil
import sqlite3 
try: 
    import cPickle as cPickle 
except: 
    import pickle as cPickle 
from string import digits
from string import maketrans
from collections import OrderedDict

#try:
#    from cStringIO import StringIO
#except:
#    from StringIO import StringIO

# 3rd party imports
import simplejson
from Bio.Seq import Seq
from Bio.Alphabet import IUPAC, generic_dna

# KBase imports
import biokbase.Transform.script_utils as script_utils
import biokbase.Transform.TextFileDecoder as TextFileDecoder
import biokbase.workspace.client 
import trns_transform_FASTA_DNA_Assembly_to_KBaseGenomeAnnotations_Assembly as assembly


def make_scientific_names_lookup(taxon_names_file=None):
    # TODO change this work with a master taxonomy tree object.  Currently requires the names file from NCBI
    #key scientific name, value is taxon object name (taxid_taxon)
    scientific_names_lookup = dict() 
 
    if os.path.isfile(taxon_names_file): 
        print "Found taxon_names_File" 
        name_f = open(taxon_names_file, 'r') 
        for name_line in name_f: 
            temp_list = re.split(r'\t*\|\t*', name_line) 
#            scientific_names_lookup[temp_list[1]] = "%s_taxon" % (str(temp_list[0])) 
            scientific_names_lookup[temp_list[1]] = temp_list[0] 
        name_f.close() 
    else:
        raise Exception("The taxon names file does not exist") 
    return scientific_names_lookup




def insert_newlines(s, every): 
    lines = [] 
    for i in xrange(0, len(s), every): 
        lines.append(s[i:i+every]) 
    return "\n".join(lines)+"\n" 

def represents_int(s):
    try: 
        int(s)
        return True
    except ValueError:
        return False


# transformation method that can be called if this module is imported
# Note the logger has different levels it could be run.  
# See: https://docs.python.org/2/library/logging.html#logging-levels
#
# The default level is set to INFO which includes everything except DEBUG
#@profile
def upload_genome(shock_service_url=None, 
                  handle_service_url=None, 
                  #output_file_name=None, 
                  #input_fasta_directory=None, 
                  input_directory=None, 
                  shock_id=None, handle_id=None, 
                  #input_file_name=None, 
                  #fasta_reference_only=False,
                  workspace_name=None,
                  workspace_service_url=None,
#                  genome_list_file=None,
                  taxon_wsname=None,
                  exclude_feature_types=list(),
#                  taxon_names_file=None,
                  taxon_reference = None,
                  release= None,
                  #              fasta_file_directory=None,
                  core_genome_name=None,
                  source=None,
                  type=None,
                  level=logging.INFO, logger=None):
    """
    Uploads CondensedGenomeAssembly
    Args:
        shock_service_url: A url for the KBase SHOCK service.
        input_fasta_directory: The directory where files will be read from.
        level: Logging level, defaults to logging.INFO.
        
    Returns:
        JSON file on disk that can be saved as a KBase workspace object.
    Authors:
        Jason Baumohl, Matt Henderson
    """

    if logger is None:
        logger = script_utils.stderrlogger(__file__)
    token = os.environ.get('KB_AUTH_TOKEN') 

    if exclude_feature_types is None:
        exclude_feature_types = list()

#    scientific_names_lookup = make_scientific_names_lookup(taxon_names_file)

    ws_client = biokbase.workspace.client.Workspace(workspace_service_url)
 
    workspace_object = ws_client.get_workspace_info({'workspace':workspace_name}) 

    workspace_id = workspace_object[0] 
    workspace_name = workspace_object[1] 
 
    taxon_ws_client = biokbase.workspace.client.Workspace(workspace_service_url)
    taxon_workspace_object = ws_client.get_workspace_info({'workspace':taxon_wsname}) 

    taxon_workspace_id = taxon_workspace_object[0] 
    taxon_workspace_name = taxon_workspace_object[1] 
 
    logger.info("Scanning for Genbank Format files.") 
 
    valid_extensions = [".gbff",".gbk",".gb",".genbank",".dat"] 
 
    files = os.listdir(os.path.abspath(input_directory)) 
    print "FILES : " + str(files)
    genbank_files = [x for x in files if os.path.splitext(x)[-1] in valid_extensions] 
 
    if (len(genbank_files) == 0): 
        raise Exception("The input directory does not have one of the following extensions %s." % (",".join(valid_extensions))) 
  
    logger.info("Found {0}".format(str(genbank_files))) 
 
    source_file_name = genbank_files[0]
    input_file_name = os.path.join(input_directory,genbank_files[0]) 
 
    if len(genbank_files) > 1: 
        # TODO if multiple files - CONCATENATE FILES HERE (sort by name)? OR Change how the byte coordinates work.
        logger.warning("Not sure how to handle multiple Genbank files in this context. Using {0}".format(input_file_name))

    print "INPUT FILE NAME :" + input_file_name + ":"

    genbank_file_boundaries = list()  
    #list of tuples: (first value record start byte position, second value record stop byte position)

    exclude_feature_types.append("source")

    if os.path.isfile(input_file_name):
        print "Found Genbank_File" 
        make_sql_in_memory = True
        dir_name = os.path.dirname(input_file_name)

        #take in Genbank file and remove all empty lines from it.
        os.rename(input_file_name,"%s/temp_file_name" % (dir_name))
        temp_file = "%s/temp_file_name" % (dir_name)

        with open(temp_file,'r') as f_in:
            with open(input_file_name,'w', buffering=2**20 ) as f_out:
                for line in f_in:
                    if line.strip():
                        f_out.write(line)
        os.remove(temp_file)

        #If file is over a 1GB need to do SQLLite on disc
        if os.stat(input_file_name) > 1073741824 :
            make_sql_in_memory = True
            
        genbank_file_handle = TextFileDecoder.open_textdecoder(input_file_name, 'ISO-8859-1') 
        start_position = 0
        current_line = genbank_file_handle.readline()
        last_line = None
        while (current_line != ''):
            last_line = current_line 
            if current_line.startswith("//"):
                end_position =  genbank_file_handle.tell() - len(current_line)
                genbank_file_boundaries.append([start_position,end_position])
#                last_start_position = start_position
                start_position = genbank_file_handle.tell()
            current_line = genbank_file_handle.readline()

        if not last_line.startswith("//"):
            end_position = genbank_file_handle.tell()
            genbank_file_boundaries.append([start_position,end_position])
    else:
        print "NO GENBANK FILE"
        sys.exit(1)

    print "Number of contigs : " + str(len(genbank_file_boundaries))
   
    organism_dict = dict() 
    organism = None
    if len(genbank_file_boundaries) < 1 :
        print "Error no genbank record found in the input file"
        sys.exit(1)
    else:
        byte_coordinates = genbank_file_boundaries[0]
        genbank_file_handle.seek(byte_coordinates[0]) 
        temp_record = genbank_file_handle.read(byte_coordinates[1] - byte_coordinates[0]) 

        record_lines = temp_record.split("\n")
        for record_line in record_lines:
            if record_line.startswith("  ORGANISM  "):
                organism = record_line[12:]
                print "Organism Line :" + record_line + ":"
                print "Organism :" + organism + ":"
                organism_dict[organism] = 1
                break

    tax_id = 0;
    tax_lineage = None;

    genome_annotation = dict()

    display_sc_name = None

    genomes_without_taxon_refs = list()
    if taxon_reference is None:
        #Get the taxon_lookup_object
        taxon_lookup = ws_client.get_objects( [{'workspace':taxon_wsname,
                                                'name':"taxon_lookup"}])
        if ((organism is not None) and (organism[0:3] in taxon_lookup[0]['data']['taxon_lookup'])):
            if organism in taxon_lookup[0]['data']['taxon_lookup'][organism[0:3]]:
                tax_id = taxon_lookup[0]['data']['taxon_lookup'][organism[0:3]][organism] 
                taxon_object_name = "%s_taxon" % (str(tax_id))
            else:
                genomes_without_taxon_refs.append(organism)
                taxon_object_name = "unknown_taxon"
                genome_annotation['notes'] = "Unable to find taxon for this organism : %s ." % (organism )
        else: 
            genomes_without_taxon_refs.append(organism)
            taxon_object_name = "unknown_taxon"
            genome_annotation['notes'] = "Unable to find taxon for this organism : %s ." % (organism ) 
        del taxon_lookup
        try: 
            taxon_info = ws_client.get_objects([{"workspace": taxon_wsname, 
                                                 "name": taxon_object_name}]) 
            taxon_id = "%s/%s/%s" % (taxon_info[0]["info"][6], taxon_info[0]["info"][0], taxon_info[0]["info"][4]) 
#            print "Found name : " + taxon_object_name + " id: " + taxon_id
#            print "TAXON OBJECT TYPE : " + taxon_info[0]["info"][2]
            if not taxon_info[0]["info"][2].startswith("KBaseGenomeAnnotations.Taxon"):
                raise Exception("The object retrieved for the taxon object is not actually a taxon object.  It is " + taxon_info[0]["info"][2])
            display_sc_name = taxon_info[0]['data']['scientific_name']
        except Exception, e: 
            raise Exception("The taxon " + taxon_object_name + " from workspace " + str(taxon_workspace_id) + " does not exist. " + str(e))
    else:
        try: 
            taxon_info = ws_client.get_objects({"object_ids":[{"ref": taxon_reference}]})
            print "TAXON OBJECT TYPE : " + taxon_info[0]["info"][2] 
            if not taxon_info[0]["info"][2].startswith("KBaseGenomeAnnotations.Taxon"):
                raise Exception("The object retrieved for the taxon object is not actually a taxon object.  It is " + taxon_info[0]["info"][2])
            display_sc_name = taxon_info[0]['data']['scientific_name']
        except Exception, e:
            raise Exception("The taxon reference " + taxon_reference + " does not correspond to a workspace object.")
    tax_lineage = taxon_info[0]["data"]["scientific_lineage"]

#EARLY BAILOUT FOR TESTING
#    sys.exit(1)

    
    #CORE OBJECT NAME WILL BE EITHER PASSED IN GENERATED (TaxID_Source)
    #Fasta file name format is taxID_source_timestamp
    time_string = str(datetime.datetime.fromtimestamp(time.time()).strftime('%Y_%m_%d_%H_%M_%S'))
    if core_genome_name is None:
        if source is None:
            source_name = "unknown_source"
        else:
            source_name = source
        if tax_id == 0:
            core_genome_name = "%s_%s" % (source_name,time_string) 
            fasta_file_name = "unknown_%s_%s.fa" % (source_name,time_string) 
        else:
            core_genome_name = "%s_%s" % (str(tax_id),source_name) 
            fasta_file_name = "%s_%s.fa" % (core_genome_name,time_string) 
    else:
        fasta_file_name = "%s_%s.fa" % (core_genome_name,time_string) 
        source_name = "unknown_source"

    print "Core Genome Name :"+ core_genome_name + ":"
    print "FASTA FILE Name :"+ fasta_file_name + ":"

    now_date = datetime.datetime.now()
        
    #Parse LOCUS line from each file and grab that meta data (also establish order of the contigs)
    locus_name_order = list() #for knowing order of the genbank files/contigs
    genbank_metadata_objects = dict() #the data structure for holding the top level metadata information of each genbank file
    contig_information_dict = dict() #the data structure for holding the top level metadata information of each genbank file for the stuff needed for making the assembly.

    #HAD TO ADD "CON" as a possible division set.  Even though that does not exist according to this documentation:
    #http://www.ncbi.nlm.nih.gov/Sitemap/samplerecord.html#GenBankDivisionB
    #Found this http://www.ncbi.nlm.nih.gov/Web/Newsltr/Fall99/contig.html , oddly suggests no sequence should be associated with this.
    genbank_division_set = {'PRI','ROD','MAM','VRT','INV','PLN','BCT','VRL','PHG','SYN','UNA','EST','PAT','STS','GSS','HTG','HTC','ENV','CON'}

    #Make the Fasta file for the sequences to be written to
    os.makedirs("temp_fasta_file_dir")
    fasta_file_name = "temp_fasta_file_dir/" +fasta_file_name
    fasta_file_handle = open(fasta_file_name, 'w')
    
    min_date = None
    max_date = None
    genbank_time_string = None
    genome_publication_dict = dict()
#    genome_comment = ''
#    genome_comment_io = StringIO()

    #Create a SQLLite database and connection.
    if make_sql_in_memory:
        sql_conn = sqlite3.connect(':memory:') 
    else:
        db_name = "GenomeAnnotation_{}.db".format(time_string) 
        sql_conn = sqlite3.connect(db_name) 

    sql_cursor = sql_conn.cursor() 

    #Create a protein and feature table.
    sql_cursor.execute('''CREATE TABLE features (feature_id text, feature_type text, sequence_length integer, feature_data blob)''')
    sql_cursor.execute('''CREATE INDEX feature_id_idx ON features (feature_id)''')
    sql_cursor.execute('''CREATE INDEX feature_type_idx ON features (feature_type)''')
    sql_cursor.execute('''CREATE INDEX seq_len_idx ON features (sequence_length)''')
    sql_cursor.execute('''CREATE TABLE proteins (protein_id text, protein_data blob)''') 
    sql_cursor.execute('''CREATE TABLE annotation_quality_warnings (warning text)''')
    sql_cursor.execute('''CREATE TABLE annotation_metadata_warnings (warning text)''')
    sql_cursor.execute('''PRAGMA synchronous=OFF''') 

    #Feature Data structures

    #Key is the gene tag (ex: gene="NAC001"), the value is a dict with feature type as the key. The value is a list of maps (one for each feature with that gene value).  
    #The internal map stores all the key value pairs of that feature.
    features_grouping_dict = dict() 
    
    #Key is the feature type.  The value is a mapping of feature specific id (may need to be auto generated) to a feature object
#    features_type_containers_dict = dict()

    #Key is the protein id (may need to be auto generated, same as CDS) to a protein object
    protein_container_dict = dict()
    protein_id_counter = 1;

    #Key is an alias, value is list of tuples (feature_container_object_name, feature_id)
    feature_lookup_dict = dict()

    #Feature_type_id_counter_dict  keeps track of the count of each time a specific id needed to be generated by the uploader and not the file.
    feature_type_id_counter_dict = dict()

    #Key is feature type, value is the number of occurances of this type. Lets me know the feature containers that will need 
    #to be made and a check to insure the counts are accurate.
    feature_type_counts = dict() 

    #Key is the feature type, value is the object reference to the feature container object.
    feature_container_references = dict()

    #Dict used if need to cleanup aliases
    reverse_feature_container_ref_lookup = dict()

    #Dict of alias source and the count
    alias_source_counts_map = dict()
    #Dict of interfeature relationship type and count of occurences.  
    #Keys "CDS_with_mRNA","CDS_with_gene","mRNA_with_CDS","mRNA_with_gene","gene_with_CDS" and "gene_with_mRNA"
    interfeature_relationship_counts_map = dict()

    genes_with_mRNA = dict()
    genes_with_CDS = dict()

    #integers used for stripping text 
    complement_len = len("complement(")
    join_len = len("join(")
    order_len = len("order(")

    print "NUMBER OF GENBANK COORDINATES: " + str(len(genbank_file_boundaries))
    for byte_coordinates in genbank_file_boundaries: 
        genbank_file_handle.seek(byte_coordinates[0]) 
        genbank_record = genbank_file_handle.read(byte_coordinates[1] - byte_coordinates[0]) 
        try:
            annotation_part, sequence_part = genbank_record.rsplit("ORIGIN",1)
        except Exception, e:
            #sequence does not exist.
            fasta_file_handle.close() 
            raise Exception("This Genbank file has at least one record without a sequence.")
            sys.exit(1) 

        #done with need for variable genbank_record. Freeing up memory
        genbank_record = None
        metadata_part, features_part = annotation_part.rsplit("FEATURES             Location/Qualifiers",1) 

        metadata_lines = metadata_part.split("\n")

        ##########################################
        #METADATA PARSING PORTION
        ##########################################
        for metadata_line in metadata_lines: 
            if metadata_line.startswith("ACCESSION   "): 
                temp = metadata_line[12:]
                accession = temp.split(' ', 1)[0]
                break

        #LOCUS line parsing
        locus_line_info = metadata_lines[0].split()
        genbank_metadata_objects[accession] = dict()
        contig_information_dict[accession] = dict()
        locus_name_order.append(accession)
        genbank_metadata_objects[accession]["number_of_basepairs"] = locus_line_info[2]
        date_text = None
        if ((len(locus_line_info)!= 7) and (len(locus_line_info)!= 8)): 
            fasta_file_handle.close()
            raise Exception("Error the record with the Locus Name of %s does not have a valid Locus line.  It has %s space separated elements when 6 to 8 are expected (typically 8)." % (locus_info_line[1],str(len(locus_line_info))))
        if locus_line_info[4].upper() != 'DNA':
            if (locus_line_info[4].upper() == 'RNA') or (locus_line_info[4].upper() == 'SS-RNA') or (locus_line_info[4].upper() == 'SS-DNA'):
                if not tax_lineage.lower().startswith("viruses") and not tax_lineage.lower().startswith("viroids"):
                    fasta_file_handle.close()
                    raise Exception("Error the record with the Locus Name of %s is RNA, but the organism does not belong to Viruses or Viroids." % (locus_line_info[1]))
            else:
                fasta_file_handle.close()
                raise Exception("Error the record with the Locus Name of %s is not valid as the molecule type of '%s' , is not 'DNA' or 'RNA'.  If it is RNA it must be a virus or a viroid." % (locus_line_info[1],locus_line_info[4]))
        if ((locus_line_info[5] in genbank_division_set) and (len(locus_line_info) == 7)) :
            genbank_metadata_objects[accession]["is_circular"] = "Unknown"
            contig_information_dict[accession]["is_circular"] = "Unknown"
            date_text = locus_line_info[6]
        elif (locus_line_info[6] in genbank_division_set  and (len(locus_line_info) == 8)) :
            date_text = locus_line_info[7]
            if locus_line_info[5] == "circular":
                genbank_metadata_objects[accession]["is_circular"] = "True"
                contig_information_dict[accession]["is_circular"] = "True"
            elif locus_line_info[5] == "linear":
                genbank_metadata_objects[accession]["is_circular"] = "False"
                contig_information_dict[accession]["is_circular"] = "False"
            else:
                genbank_metadata_objects[accession]["is_circular"] = "Unknown"
                contig_information_dict[accession]["is_circular"] = "Unknown"
        else:
            date_text = locus_line_info[5]

        try:
            record_time = datetime.datetime.strptime(date_text, '%d-%b-%Y')
            if min_date == None:
                min_date = record_time
            elif record_time < min_date:
                min_date = record_time
            if max_date == None:
                max_date = record_time
            elif record_time > max_date:
                max_date = record_time

        except ValueError:
            fasta_file_handle.close()
            exception_string = "Incorrect date format, should be 'DD-MON-YYYY' , attempting to parse the following as a date: %s , the locus line elements: %s " % (date_text, ":".join(locus_line_info))
#            raise ValueError("Incorrect date format, should be 'DD-MON-YYYY' , attempting to parse the following as a date:" + date_text)
            raise ValueError(exception_string)
            sys.exit(1)

        genbank_metadata_objects[accession]["external_source_origination_date"] = date_text

        num_metadata_lines = len(metadata_lines)
        metadata_line_counter = 0

        for metadata_line in metadata_lines:
            if metadata_line.startswith("DEFINITION  "):
                definition = metadata_line[12:]
                definition_loop_counter = 1
                if ((metadata_line_counter + definition_loop_counter)<= num_metadata_lines):
                    next_line = metadata_lines[metadata_line_counter + definition_loop_counter]
                    while (next_line.startswith("            ")) and ((metadata_line_counter + definition_loop_counter)<= num_metadata_lines) :
                        definition = "%s %s" % (definition,next_line[12:])
                        definition_loop_counter += 1
                        if ((metadata_line_counter + definition_loop_counter)<= num_metadata_lines):
                            next_line = metadata_lines[metadata_line_counter + definition_loop_counter]
                        else:
                            break
                genbank_metadata_objects[accession]["definition"] = definition 
                contig_information_dict[accession]["definition"] = definition 
            elif metadata_line.startswith("  ORGANISM  "): 
                organism = metadata_line[12:] 
                if organism not in organism_dict:
                    fasta_file_handle.close()
                    raise ValueError("There is more than one organism represented in these Genbank files, they do not represent single genome. First record's organism is %s , but %s was also found" 
                                     % (str(organism_dict.keys()),organism)) 
                    sys.exit(1) 
            elif metadata_line.startswith("COMMENT     "):
                comment = metadata_line[12:] 
                comment_loop_counter = 1 
                if ((metadata_line_counter + comment_loop_counter)<= num_metadata_lines):
                    next_line = metadata_lines[metadata_line_counter + comment_loop_counter] 
                    while (next_line.startswith("            ")) : 
                        comment = "%s %s" % (comment,next_line[12:]) 
                        comment_loop_counter += 1 
                        if ((metadata_line_counter + comment_loop_counter)<= num_metadata_lines):
                            next_line = metadata_lines[metadata_line_counter + comment_loop_counter]
                        else:
                            break
#                genome_comment = "%s<%s :: %s> " % (genome_comment,accession,comment)
#                genome_comment_io.write("<%s :: %s> " % (accession,comment))
            elif metadata_line.startswith("REFERENCE   "):
                #PUBLICATION SECTION (long)
                authors = ''
                title = ''
                journal = ''
                pubmed = ''
                consortium = ''
                publication_key = metadata_line

                reference_loop_counter = 1
                if ((metadata_line_counter + reference_loop_counter)<= num_metadata_lines): 
                    next_line = metadata_lines[metadata_line_counter + reference_loop_counter] 
                # while (next_line and re.match(r'\s', next_line) and not nextline[0].isalpha()):
                while (next_line and re.match(r'\s', next_line)):
                    publication_key += next_line
                    if next_line.startswith("  AUTHORS   "):
                        authors = next_line[12:] 
                        reference_loop_counter += 1
                        if ((metadata_line_counter + reference_loop_counter)<= num_metadata_lines):
                            next_line = metadata_lines[metadata_line_counter + reference_loop_counter] 
                        else:
                            break
                        while (next_line.startswith("            ")) :     
                            authors = "%s %s" % (authors,next_line[12:]) 
                            reference_loop_counter += 1
                            if ((metadata_line_counter + reference_loop_counter)<= num_metadata_lines): 
                                next_line = metadata_lines[metadata_line_counter + reference_loop_counter] 
                            else: 
                                break 
                    elif next_line.startswith("  TITLE     "):
                        title = next_line[12:]
                        reference_loop_counter += 1
                        if ((metadata_line_counter + reference_loop_counter)<= num_metadata_lines):
                            next_line = metadata_lines[metadata_line_counter + reference_loop_counter]
                        else:
                            break
                        while (next_line.startswith("            ")) :
                            title = "%s %s" % (title,next_line[12:])
                            reference_loop_counter += 1
                            if ((metadata_line_counter + reference_loop_counter)<= num_metadata_lines):
                                next_line = metadata_lines[metadata_line_counter + reference_loop_counter]
                            else:
                                break
                    elif next_line.startswith("  JOURNAL   "):
                        journal = next_line[12:]
                        reference_loop_counter += 1
                        if ((metadata_line_counter + reference_loop_counter)<= num_metadata_lines):
                            next_line = metadata_lines[metadata_line_counter + reference_loop_counter]
                        else:
                            break
                        while (next_line.startswith("            ")) :
                            journal = "%s %s" % (journal,next_line[12:])
                            reference_loop_counter += 1
                            if ((metadata_line_counter + reference_loop_counter)<= num_metadata_lines):
                                next_line = metadata_lines[metadata_line_counter + reference_loop_counter]
                            else:
                                break
                    elif next_line.startswith("   PUBMED   "): 
                        pubmed = next_line[12:] 
                        reference_loop_counter += 1
                        if ((metadata_line_counter + reference_loop_counter)<= num_metadata_lines):
                            next_line = metadata_lines[metadata_line_counter + reference_loop_counter]
                        else:
                            break
                        while (next_line.startswith("            ")) : 
                            pubmed = "%s %s" % (journal,next_line[12:]) 
                            reference_loop_counter += 1
                            if ((metadata_line_counter + reference_loop_counter)<= num_metadata_lines): 
                                next_line = metadata_lines[metadata_line_counter + reference_loop_counter] 
                            else: 
                                break 
                    elif next_line.startswith("  CONSRTM   "):
                        consortium = next_line[12:]
                        reference_loop_counter += 1
                        if ((metadata_line_counter + reference_loop_counter)<= num_metadata_lines): 
                            next_line = metadata_lines[metadata_line_counter + reference_loop_counter]
                        else:
                            break 
                        while (next_line.startswith("            ")) : 
                            consortium = "%s %s" % (journal,next_line[12:]) 
                            reference_loop_counter += 1
                            if ((metadata_line_counter + reference_loop_counter)<= num_metadata_lines):
                                next_line = metadata_lines[metadata_line_counter + reference_loop_counter]
                            else:
                                break
                    else:
                        reference_loop_counter += 1
                        if ((metadata_line_counter + reference_loop_counter)<= num_metadata_lines):
                            next_line = metadata_lines[metadata_line_counter + reference_loop_counter]
                        else:
                            break
                #Done grabbing reference lines, time to build the reference object.

                pubmed_link = ''
                publication_source = ''
                publication_date = ''
                if pubmed != '':
                    publication_source = "PubMed"
                elif consortium != '':
                    publication_source = consortium
                try:
                    pubmed = int(pubmed)
                except ValueError:
                    pubmed = 0
                if pubmed != 0:
                    pubmed_link = "http://www.ncbi.nlm.nih.gov/pubmed/%s" % str(pubmed)
                if journal != '':
                    potential_date_regex = r'(?<=\().+?(?=\))'
                    potential_dates = re.findall(potential_date_regex, journal)
                    
                    for potential_date in reversed(potential_dates):                        
                        try:
                            record_time = datetime.datetime.strptime(potential_date, '%d-%b-%Y')
                            if now_date > record_time:
                                publication_date = potential_date
                                break
                        except ValueError:
                            try:
                                record_time = datetime.datetime.strptime(potential_date, '%b-%Y')
                                if now_date > record_time:
                                    publication_date = potential_date
                                    break       
                            except ValueError:
                                try:
                                    record_time = datetime.datetime.strptime(potential_date, '%Y')
                                    if now_date > record_time:
                                        publication_date = potential_date
                                        break
                                except ValueError:
                                    next
                publication = [pubmed,publication_source,title,pubmed_link,publication_date,authors,journal]
                genome_publication_dict[publication_key] = publication
                #END OF PUBLICATION SECTION

            metadata_line_counter += 1

        if len(genome_publication_dict) > 0 :
            genome_annotation["publications"] = genome_publication_dict.values() 

        ##################################################################################################
        #MAKE SEQUENCE PART INTO CONTIG WITH NO INTERVENING SPACES OR NUMBERS
        ##################################################################################################
        sequence_part = re.sub('[0-9]+', '', sequence_part)
        sequence_part = re.sub('\s+','',sequence_part)
        sequence_part = sequence_part.replace("?","")

        contig_length = len(sequence_part)
        if contig_length == 0:
            fasta_file_handle.close() 
            raise Exception("The genbank record %s does not have any sequence associated with it." % (accession))
            

        ##################################################################################################
        #FEATURE ANNOTATION PORTION - Build up datastructures to be able to build feature containers.
        ##################################################################################################
        #print "GOT TO FEATURE PORTION"
        features_lines = features_part.split("\n") 

        num_feature_lines = len(features_lines)
        features_list = list()

        #break up the features section into individual features.
        for feature_line_counter in range(0,(num_feature_lines)):
            feature_line = features_lines[feature_line_counter]
            if ((not feature_line.startswith("                     ")) and (feature_line.startswith("     ")) and (feature_line[5:7].strip() != "")):
                #Means a new feature:
                #
                current_feature_string = feature_line
                while ((feature_line_counter + 1) < num_feature_lines) and (features_lines[(feature_line_counter + 1)].startswith("                     ")): 
                    feature_line_counter += 1 
                    feature_line = features_lines[feature_line_counter]
                    current_feature_string += " %s" % (feature_line)

                features_list.append(current_feature_string)

            elif ((feature_line_counter + 1) < num_feature_lines): 
                feature_line_counter += 1 
                feature_line = features_lines[feature_line_counter]
        
        #Go through each feature and determine key value pairs, properties and importantly the id to use to group for interfeature_relationships.
        for feature_text in features_list:
            feature_object = dict()
            #split the feature into the key value pairs. "/" denotes start of a new key value pair.
            feature_key_value_pairs_list = feature_text.split("                     /")
            feature_header = feature_key_value_pairs_list.pop(0)
            if len(feature_header[:5].strip()) != 0:
                continue
            coordinates_info = feature_header[21:] 
            feature_type = feature_header[:21] 
            feature_type = feature_type.strip().replace(" ","_")
            if feature_type in exclude_feature_types:
#            if feature_type == "source":
                #skip source feature types.
                continue
            feature_object["type"] = feature_type


            quality_warnings = list() #list of warnings about the feature. Can do more with this at a later time.
            feature_keys_present_dict = dict() #dict of keys present in the feature

            ############################################
            #DETERMINE ID TO USE FOR THE FEATURE OBJECT
            ############################################                                                                                                                                      
#            if feature_type not in features_type_containers_dict:
#                features_type_containers_dict[feature_type] = dict()
            feature_id = None 
            #MAKING ALL IDS UNIQUE ACROSS THE GENOME.
            if feature_type not in feature_type_id_counter_dict:
                feature_type_id_counter_dict[feature_type] = 1;
                feature_id = "%s_%s" % (feature_type,str(1)) 
            else: 
                feature_type_id_counter_dict[feature_type] += 1; 
                feature_id = "%s_%s" % (feature_type,str(feature_type_id_counter_dict[feature_type]))

            for feature_key_value_pair in feature_key_value_pairs_list: 
                #the key value pair removing unnecessary white space (including new lines as these often span multiple lines)
                temp_string = re.sub( '\s+', ' ', feature_key_value_pair ).strip() 
                try: 
                    key, value = temp_string.split('=', 1) 
                except Exception, e: 
                    #Does not follow key value pair structure.  This unexpected. Skipping.
                    key = temp_string
                    value = ""

                value = re.sub(r'^"|"$', '', value.strip())
                feature_keys_present_dict[key.strip()] = 1

            coordinates_info = re.sub( '\s+', '', coordinates_info ).strip()
            original_coordinates = coordinates_info
            coordinates_list = list()
            apply_complement_to_all = False
            need_to_reverse_locations = False
            has_odd_coordinates = False
            can_not_process_feature = False
            if coordinates_info.startswith("complement") and coordinates_info.endswith(")"): 
                apply_complement_to_all = True
                need_to_reverse_locations = True
                coordinates_info = coordinates_info[complement_len:-1]
            if coordinates_info.startswith("join") and coordinates_info.endswith(")"):
                coordinates_info = coordinates_info[join_len:-1]
            if coordinates_info.startswith("order") and coordinates_info.endswith(")"):
                coordinates_info = coordinates_info[order_len:-1]
                has_odd_coordinates = True
                temp_warning = "%s has the rare 'order' coordinate. The sequence was joined together because KBase does not allow for a non contiguous resulting sequence with multiple locations for a feature." % (feature_id)
                quality_warnings.append(temp_warning)
                #annotation_metadata_warnings.append(temp_warning)
                sql_cursor.execute("insert into annotation_metadata_warnings values(:warning)",(temp_warning,))
            coordinates_list = coordinates_info.split(",")
            last_coordinate = 0
            dna_sequence_length = 0
            dna_sequence = ''
            locations = list()#list of location objects
            for coordinates in coordinates_list:
                apply_complement_to_current = False
                if coordinates.startswith("complement") and coordinates.endswith(")"): 
                    apply_complement_to_current = True 
                    coordinates = coordinates[complement_len:-1]
                #Look for and handle odd coordinates
                if (("<" in coordinates) or (">" in coordinates)):
                    has_odd_coordinates = True
                    temp_warning = "%s has a '<' or a '>' in the coordinates.  This means the feature starts or ends beyond the known sequence." % (feature_id)
                    quality_warnings.append(temp_warning)
                    #annotation_metadata_warnings.append(temp_warning)
                    sql_cursor.execute("insert into annotation_metadata_warnings values(:warning)",(temp_warning,))
                    coordinates= re.sub('<', '', coordinates)
                    coordinates= re.sub('>', '', coordinates)


                period_count = coordinates.count('.')
                if ((period_count == 2) and (".." in coordinates)):
                    start_pos, end_pos = coordinates.split('..', 1)                    
                elif period_count == 0:
                    start_pos = coordinates
                    end_pos = coordinates
                elif period_count == 1:
                    start_pos, end_pos = coordinates.split('.', 1) 
                    has_odd_coordinates = True
                    temp_warning = "%s has a single period in the original coordinate this indicates that the exact location is unknown but that it is one of the bases between bases %s and %s, inclusive.  Note the entire sequence range has been put into this feature." % (feature_id, str(start_pos),str(end_pos))
                    quality_warnings.append(temp_warning)
                    #annotation_metadata_warnings.append(temp_warning)
                    sql_cursor.execute("insert into annotation_metadata_warnings values(:warning)",(temp_warning,))
                elif period_count > 2 :
                    can_not_process_feature = True
                else:
                    can_not_process_feature = True
                if "^" in coordinates:
                    start_pos, end_pos = coordinates.split('^', 1) 
                    has_odd_coordinates = True
                    temp_warning = "%s is between bases.  It points to a site between bases %s and %s, inclusive.  Note the entire sequence range has been put into this feature." % (feature_id, str(start_pos),str(end_pos))
                    quality_warnings.append(temp_warning)
                    #annotation_metadata_warnings.append(temp_warning)       
                    sql_cursor.execute("insert into annotation_metadata_warnings values(:warning)",(temp_warning,))

                if not can_not_process_feature:
                    if (represents_int(start_pos) and represents_int(end_pos)):
                        if int(start_pos) > int(end_pos):
                            fasta_file_handle.close() 
                            print "FEATURE TEXT: " + feature_text
                            raise Exception("The genbank record %s has coordinates that are out of order. Start coordinate %s is bigger than End coordinate %s. Should be ascending order." % (accession, str(start_pos), str(end_pos)))

#CANT COUNT ON THEM BEING IN ASCENDING POSITIONAL ORDER
#                    if (int(start_pos) < last_coordinate or int(end_pos) < last_coordinate) and ("trans_splicing" not in feature_keys_present_dict) :
#                        fasta_file_handle.close()
#                        raise Exception("The genbank record %s has coordinates that are out of order. Start coordinate %s and/or End coordinate %s is larger than the previous coordinate %s within this feature. Should be ascending order since this is not a trans_splicing feature." % (accession, str(start_pos), str(end_pos),str(last_coordinate)))

                        if (int(start_pos) > contig_length) or (int(end_pos) > contig_length):
                            fasta_file_handle.close() 
                            raise Exception("The genbank record %s has coordinates (start: %s , end: %s) that are longer than the sequence length %s." % \
                                            (accession,str(start_pos), int(end_pos),str(contig_length)))

                        segment_length = (int(end_pos) - int(start_pos)) + 1
                        dna_sequence_length += segment_length
                        temp_sequence = sequence_part[(int(start_pos)-1):int(end_pos)] 
                        strand = "+"
                        location_start = int(start_pos)
                        if apply_complement_to_current or apply_complement_to_all: 
                            my_dna = Seq(temp_sequence, IUPAC.ambiguous_dna)
                            my_dna = my_dna.reverse_complement()
                            temp_sequence = str(my_dna).upper()      
                            strand = "-"
                            location_start = location_start + (segment_length - 1)
                        if apply_complement_to_all:
                            dna_sequence =  temp_sequence + dna_sequence 
                        else:
                            dna_sequence +=  temp_sequence 

                        locations.append([accession,location_start,strand,segment_length]) 
                    else:
                        #no valid coordinates
                        print "Feature text : " + feature_text + ":"
                        fasta_file_handle.close() 
                        raise Exception("The genbank record %s contains coordinates that are not valid number(s).  Feature text is : %s" % (accession,feature_text)) 

                    last_coordinate = int(end_pos)

            if has_odd_coordinates:
                    quality_warnings.insert(0,"Note this feature contains some atypical coordinates, see the rest of the warnings for details : %s" % (original_coordinates))
            if can_not_process_feature: 
                #skip source feature types.
                continue

            
            dna_sequence = dna_sequence.upper()

            if len(locations) > 0:
                if need_to_reverse_locations and (len(locations) > 1):
                    locations.reverse()
            feature_object["locations"]=locations

            feature_object["dna_sequence_length"] = dna_sequence_length
            feature_object["dna_sequence"] = dna_sequence
            try:
                feature_object["md5"] = hashlib.md5(dna_sequence).hexdigest() 
            except Exception, e:
#                print "THE FEATURE TEXT IS : %s" % (feature_text)
#                print "THE FEATURE SEQUENCE IS : %s : " % (dna_sequence)
#                print "Help %s" % help(dna_sequence)
                raise Exception(e)

            if feature_type in feature_type_counts:
                feature_type_counts[feature_type] += 1
            else:
                feature_type_counts[feature_type] = 1     
            
            #Need to determine id for the feature : order selected by gene, then locus.
            alias_dict = dict() #contains locus_tag, gene, gene_synonym, dbxref, then value is list of sources.
            inference = ""
            notes = ""
            additional_properties = dict()
            feature_specific_id = None
            product = None
            EC_number = None

            for feature_key_value_pair in feature_key_value_pairs_list:
                #the key value pair removing unnecessary white space (including new lines as these often span multiple lines)
                temp_string = re.sub( '\s+', ' ', feature_key_value_pair ).strip()

                try: 
                    key, value = temp_string.split('=', 1) 
                except Exception, e: 
                    #Does not follow key value pair structure.  This unexpected. Skipping.
                    if temp_string != "trans_splicing":
                        temp_warning = "%s has the following feature property does not follow the expected key=value format : %s" % (feature_id, temp_string) 
                        quality_warnings.append(temp_warning)
                        #annotation_metadata_warnings.append(temp_warning)
                        sql_cursor.execute("insert into annotation_metadata_warnings values(:warning)",(temp_warning,))       
                    key = temp_string 
                    value = "" 

                key = key.strip()
                value = re.sub(r'^"|"$', '', value.strip())

                if key == "gene":
                    feature_object["gene"] = value 
                    if value in alias_dict and ("Genbank Gene" not in alias_dict[value]) :
                        alias_dict[value].append("Genbank Gene")
                    else:
                        alias_dict[value]=["Genbank Gene"] 
                elif key == "locus_tag":
                    feature_object["locus_tag"] = value 
                    if feature_type == "gene":
                        feature_object["feature_specific_id"] = value
                    if value in alias_dict and ("Genbank Locus Tag" not in alias_dict[value]) :
                        alias_dict[value].append("Genbank Locus Tag")
                    else:
                        alias_dict[value]=["Genbank Locus Tag"] 
                elif key == "old_locus_tag" or key == "standard_name":
                    if value in alias_dict and (("Genbank %s" % (key)) not in alias_dict[value]) :
                        alias_dict[value].append("Genbank %s" % (key))
                    else:
                        alias_dict[value]=[("Genbank %s" % (key))] 
                elif key == "gene_synonym":
                    synonyms = value.split(';') 
                    for i in synonyms:
                        i = i.strip()
                        if i in alias_dict and ("Genbank Gene Synonym" not in alias_dict[i]) :
                            alias_dict[i].append("Genbank Gene Synonym")
                        else:
                            alias_dict[i]=["Genbank Gene Synonym"]
                elif (key == "transcript_id"):
                    if feature_type == "mRNA":
                        feature_object["feature_specific_id"] = value 
                    if value in alias_dict and ("Genbank Transcript ID" not in alias_dict[value]) :
                        alias_dict[value].append("Genbank Transcript ID")
                    else:
                        alias_dict[value]=["Genbank Transcript ID"]
                elif (key == "protein_id"):
                    if feature_type == "CDS":
                        feature_object["feature_specific_id"] = value 
                    if value in alias_dict and ("Genbank Protein ID" not in alias_dict[value]) :
                        alias_dict[value].append("Genbank Protein ID")
                    else:
                        alias_dict[value]=["Genbank Protein ID"]
                elif (key == "db_xref"):
                    try:
                        db_xref_source, db_xref_value = value.strip().split(':',1)
                    except Exception, e: 
                        db_xref_source = "Unknown"
                        db_xref_value = value.strip()
                    if db_xref_value.strip() in alias_dict: 
                        if (db_xref_source.strip() not in alias_dict[db_xref_value.strip()]) :
                            alias_dict[db_xref_value.strip()].append(db_xref_source.strip())
                    else:
                        alias_dict[db_xref_value.strip()]=[db_xref_source.strip()]
                elif (key == "inference"):
                    if inference != "":
                        inference += ";"
                    inference += value
                elif (key == "note"):
                    if notes != "":
                        notes += ";"
                    notes += value
                elif (key == "translation"):
                    #
                    # TODO
                    #NOTE THIS IS A PLACE WHERE A QUALITY WARNING CHECK CAN BE DONE, 
                    #see if translation is accurate.(codon start (1,2,3) may need to be used)
                    #
                    value = re.sub('\s+','',value)
                    feature_object["translation"] = value 
                elif ((key == "function") and (value is not None) and (value.strip() == "")) :
                    feature_object["function"] = value
                elif (key == "product"):
                    product = value
                    additional_properties[key] = value
                elif (key == "trans_splicing"):
                    feature_object["trans_splicing"] = 1
                elif (key == "EC_number") and feature_type == "CDS":
                    EC_number = value
                else:
                    if key in additional_properties:
                        additional_properties[key] =  "%s::%s" % (additional_properties[key],value)
                    else:
                        additional_properties[key] = value


            if len(additional_properties) > 0:
                feature_object["additional_properties"] = additional_properties
            if len(notes) > 0:
                feature_object["notes"] = notes
            if len(inference) > 0:
                feature_object["inference"] = inference
            if len(alias_dict) > 0:
                feature_object["aliases"] = alias_dict
            if ("function" not in feature_object) and (product is not None):
                feature_object["function"] = product

            feature_object["quality_warnings"] = quality_warnings


#            ############################################
#            #DETERMINE ID TO USE FOR THE FEATURE OBJECT
#            ############################################
#            if feature_type not in features_type_containers_dict:
#                features_type_containers_dict[feature_type] = dict()
#            feature_id = None

#OLD WAY TRIED TO USE ID FROM THE FEATURE, UNIQUENESS ONLY GUARANTEED WITH FEATURE CONTAINER AND NOT ACROSS THE GENOME ANNOTATION
#            if "feature_specific_id" not in feature_object:
#                if "locus_tag" not in feature_object:
#                    if feature_type not in feature_type_id_counter_dict:
#                        feature_type_id_counter_dict[feature_type] = 1;
#                        feature_id = "%s_%s" % (feature_type,str(1))
#                    else:
#                        feature_type_id_counter_dict[feature_type] += 1;
#                        feature_id = "%s_%s" % (feature_type,str(feature_type_id_counter_dict[feature_type]))
#                else:
#                    feature_id = feature_object["locus_tag"]
#            else:
#                feature_id = feature_object["feature_specific_id"]
#            if feature_id in features_type_containers_dict[feature_type]:
#                #Insure that no duplicate ids exist
#                if feature_type not in feature_type_id_counter_dict:
#                    feature_type_id_counter_dict[feature_type] = 1;
#                    feature_id = "%s_%s" % (feature_type,str(1))
#                else: 
#                    feature_type_id_counter_dict[feature_type] += 1;
#                    feature_id = "%s_%s" % (feature_type,str(feature_type_id_counter_dict[feature_type]))
#END OLD WAY


##NEW WAY:  MAKING ALL IDS UNIQUE ACROSS THE GENOME.
#            if feature_type not in feature_type_id_counter_dict:
#                feature_type_id_counter_dict[feature_type] = 1;
#                feature_id = "%s_%s" % (feature_type,str(1))
#            else: 
#                feature_type_id_counter_dict[feature_type] += 1;
#                feature_id = "%s_%s" % (feature_type,str(feature_type_id_counter_dict[feature_type]))
##END NEW WAY

#            if feature_type not in features_type_containers_dict:
#                features_type_containers_dict[feature_type]=dict()
            feature_object["feature_id"] = feature_id

#            features_type_containers_dict[feature_type][feature_id] = feature_object

            sanitized_feature_type = re.sub(r'\W+', '', feature_type)
            feature_container_object_name = "%s_feature_container_%s" % (core_genome_name, sanitized_feature_type)
            feature_container_ref = "%s/%s" % (workspace_name,feature_container_object_name)
            reverse_feature_container_ref_lookup[feature_container_ref]=feature_type

            if feature_id not in feature_lookup_dict: 
                feature_lookup_dict[feature_id] = list() 
            feature_lookup_dict[feature_id].append([feature_container_ref,feature_id])

            if "aliases" in feature_object: 
                for alias in feature_object["aliases"]:
                    if alias not in feature_lookup_dict:
                        feature_lookup_dict[alias] = list()
                    feature_lookup_dict[alias].append([feature_container_ref,feature_id])
                    for alias_source in feature_object["aliases"][alias]:
                        if alias_source not in alias_source_counts_map:
                            alias_source_counts_map[alias_source] = 1
                        else:
                            alias_source_counts_map[alias_source] = alias_source_counts_map[alias_source] + 1

            #######################
            # MAKE GROUPINGS TO HELP DETERMINE INTERFEATURE RELATIONSHIPS
            ######################
            if feature_type in ['CDS','mRNA','gene']:
                #TRY to put into grouping if possible.  If not the interfeature relationships will not be able to be determined.
                if "locus_tag" in feature_object:
                    if feature_object["locus_tag"] not in features_grouping_dict:
                        features_grouping_dict[feature_object["locus_tag"]]=dict()
                    if feature_type not in features_grouping_dict[feature_object["locus_tag"]]:
                        features_grouping_dict[feature_object["locus_tag"]][feature_type]= [feature_id]
                    else:
                        features_grouping_dict[feature_object["locus_tag"]][feature_type].append(feature_id)
                if "gene" in feature_object: 
                    if "locus_tag" in feature_object and feature_object["locus_tag"] != feature_object["gene"]:
                        if feature_object["gene"] not in features_grouping_dict:
                            features_grouping_dict[feature_object["gene"]]=dict()
                        if feature_type not in features_grouping_dict[feature_object["gene"]]:
                            features_grouping_dict[feature_object["gene"]][feature_type]= [feature_id]
                        else:
                            features_grouping_dict[feature_object["gene"]][feature_type].append(feature_id)
                    elif "locus_tag" not in feature_object:
                        if feature_object["gene"] not in features_grouping_dict:
                            features_grouping_dict[feature_object["gene"]]=dict()
                        if feature_type not in features_grouping_dict[feature_object["gene"]]:
                            features_grouping_dict[feature_object["gene"]][feature_type]= [feature_id]
                        else:
                            features_grouping_dict[feature_object["gene"]][feature_type].append(feature_id)


            #############################
            #build up protein object
            #############################
            if feature_type == 'CDS':
                #GET TRANSLATION OF THE CDS.  IF THE GENBANK FILE DOES NOT HAVE IT.  

                #Build up the protein object for the protein container
                protein_object = dict()
                protein_id = "protein_%s" % (str(protein_id_counter))
                protein_id_counter += 1
                protein_object["protein_id"] = protein_id
                add_protein = True

                # TODO could add check to see if translation is accurate.  
                # DO GENERIC TRANSLATION FOR NOW (REALLY NEED TO GET TAXONOMY OBJECT AND LOOKUP ALPHABET
                # SEE http://biopython.org/wiki/Seq#Translation
                # ADD CHECK LATER AND WARNINGS IF THE TRANSLATION IN FILE AND FROM DNA SEQUENCE DO NOT MATCH

                if "translation" in feature_object:
                    protein_object["amino_acid_sequence"] = feature_object["translation"].upper()
                else:
                    if "dna_sequence" in feature_object:
                        coding_dna = Seq(feature_object["dna_sequence"], generic_dna)
                        aa_seq = coding_dna.translate()
                        protein_object["amino_acid_sequence"] = str(aa_seq[0:].upper())
                    else:
                        # TODO.  REMOVE PROTEIN REF FROM CDS PROPERTIES?
                        add_protein = false
                
                if add_protein:
                    if "function" in feature_object:
                        protein_object["function"] = feature_object["function"]
                    if "aliases" in feature_object:
                        protein_object["aliases"] = feature_object["aliases"]
                    else:
                        #Have to set to empty dict (since it is required field in spec.  Probably need to make it optional.)
                        protein_object["aliases"] = dict()

                    protein_object["md5"] = hashlib.md5(protein_object["amino_acid_sequence"]).hexdigest()
                    protein_container_dict[protein_object["protein_id"]] = protein_object
                    protein_container_object_name = "%s_protein_container" % (core_genome_name)
#                    if "CDS_properties" not in features_type_containers_dict["CDS"][feature_id]: 
#                        features_type_containers_dict["CDS"][feature_id]["CDS_properties"] = dict() 
                    if "CDS_properties" not in feature_object: 
                        feature_object["CDS_properties"] = dict() 
                    protein_ref = "%s/%s" % (workspace_name,protein_container_object_name)
                    feature_object["CDS_properties"]["codes_for_protein_ref"] = [protein_ref,protein_id]
                    if EC_number is not None:
                        feature_object["CDS_properties"]["EC_Number"] = EC_number
                    #NEED TO MAKE PICKLED PROTEIN ENTRY IN DB
                    pickled_protein = cPickle.dumps(protein_object, cPickle.HIGHEST_PROTOCOL) 
                    sql_cursor.execute("insert into proteins values(:protein_id, :protein_data)", 
                                       (protein_id, sqlite3.Binary(pickled_protein),)) 

            ########################################
            #CLEAN UP UNWANTED FEATURE KEYS
            #######################################
            if "locus_tag" in feature_object: 
                del feature_object["locus_tag"]
            if "gene" in feature_object: 
                del feature_object["gene"]
            if "feature_specific_id" in feature_object: 
                del feature_object["feature_specific_id"]
            if "translation" in feature_object: 
                del feature_object["translation"]
            

            #MAKE ENTRY INTO THE FEATURE TABLE
            pickled_feature = cPickle.dumps(feature_object, cPickle.HIGHEST_PROTOCOL) 
            sql_cursor.execute("insert into features values(:feature_id, :feature_type , :sequence_length, :feature_data)", 
                               (feature_id, feature_type, feature_object["dna_sequence_length"], sqlite3.Binary(pickled_feature),))
            
#        for feature_type in feature_type_counts:
#            print "Feature " + feature_type + "  count: " + str(feature_type_counts[feature_type])


        ##################################################################################################
        #SEQUENCE PARSING PORTION  - Write out to Fasta File
        ##################################################################################################

#        print "The len of sequence part is: " + str(len(sequence_part))
#        print "The number from the record: " + genbank_metadata_objects[accession]["number_of_basepairs"]        
#        print "First 100 of sequence part : " + sequence_part[0:100] 
        fasta_file_handle.write(">{}\n".format(accession))
        #write 80 nucleotides per line
        fasta_file_handle.write(insert_newlines(sequence_part,80))
        
    fasta_file_handle.close()
    if min_date == max_date:
        genbank_time_string = min_date.strftime('%d-%b-%Y').upper()
    else:
        genbank_time_string = "%s to %s" %(min_date.strftime('%d-%b-%Y').upper(), max_date.strftime('%d-%b-%Y').upper())


    ##########################################
    #ASSEMBLY CREATION PORTION  - consume Fasta File
    ##########################################

    logger.info("Calling FASTA to Assembly Uploader")
    assembly_reference = "%s/%s_assembly" % (workspace_name,core_genome_name)
    try:
        fasta_working_dir = str(os.getcwd()) + "/temp_fasta_file_dir"

        print "HANDLE SERVICE URL " + handle_service_url
        assembly.upload_assembly(shock_service_url = shock_service_url,
                                 handle_service_url = handle_service_url,
                                 input_directory = fasta_working_dir,
                                 #                  shock_id = args.shock_id,
                                 #                  handle_id = args.handle_id,
                                 #                  input_mapping = args.input_mapping, 
                                 workspace_name = workspace_name,
                                 workspace_service_url = workspace_service_url,
                                 taxon_reference = taxon_id,
                                 assembly_name = "%s_assembly" % (core_genome_name),
                                 source = source_name,
                                 contig_information_dict = contig_information_dict,
                                 date_string = genbank_time_string,
                                 logger = logger)
        shutil.rmtree(fasta_working_dir)
    except Exception, e: 
        logger.exception(e) 
        sys.exit(1) 

    logger.info("Assembly Uploaded")

    ####################################
    #DETERMINE INTERFEATURE RELATIONSHIPS
    #Go through each feature grouping and determine the interfeature relationships.  Then build up the feature objects for the feature containers
    #Key is the locus tag first, then the gene tag (ex: gene="NAC001"), the value is a dict with feature type as the key. 
    #The value is a list of feature_ids  
    ###################################

    print "Total Groupings length : " + str(len(features_grouping_dict))
    running_grouping_elements_count = 0
    groupings_without_three_levels = 0

    #Debugging variables, see if data assumptions are holding true.
    unequal_cds_mrna_count = 0
    inner_unequal_cds_mrna_count = 0

    #GO through each grouping id and determine the interfeature relationships
#    sql_cursor.execute("select count(*) from features") 
#    for row in sql_cursor: 
#        print "Total feature count in sql : " + str(row[0])

    for feature_grouping_id in features_grouping_dict:
        num_genes_present = 0
        num_cds_present = 0
        num_mrna_present = 0
        
        cds_features = dict()
        mrna_features = dict()
        gene_features = dict()

        if "CDS" in features_grouping_dict[feature_grouping_id]:
            num_cds_present = len(features_grouping_dict[feature_grouping_id]["CDS"])
            if num_cds_present > 0:
                sql_cursor.execute("select feature_id, feature_data from features where feature_id IN (" + 
                                   ",".join(["?"]*num_cds_present)+")",
                                   (features_grouping_dict[feature_grouping_id]["CDS"]),)
                for row in sql_cursor:
                    cds_features[row[0]] =  cPickle.loads(str(row[1]))
        if "mRNA" in features_grouping_dict[feature_grouping_id]:
            num_mrna_present = len(features_grouping_dict[feature_grouping_id]["mRNA"])
            if num_mrna_present > 0:
                sql_cursor.execute("select feature_id, feature_data from features where feature_id IN (" + 
                                   ",".join(["?"]*num_mrna_present)+")",
                                   (features_grouping_dict[feature_grouping_id]["mRNA"]),)
                for row in sql_cursor:
                    mrna_features[row[0]] =  cPickle.loads(str(row[1]))
        if "gene" in features_grouping_dict[feature_grouping_id]:
            num_genes_present = len(features_grouping_dict[feature_grouping_id]["gene"])
            if num_genes_present > 0:
                sql_cursor.execute("select feature_id, feature_data from features where feature_id IN (" + 
                                   ",".join(["?"]*num_genes_present)+")",
                                   (features_grouping_dict[feature_grouping_id]["gene"]),)
                for row in sql_cursor:
                    gene_features[row[0]] =  cPickle.loads(str(row[1]))        


        #####################################################
        #DO Gene relationships (to and from the mRNA and CDS)
        #####################################################
        if num_genes_present > 1:
            #THIS COULD CHANGE THE DOWN THE LINE (NOT GOING TO IMPLEMENT THE LOGIC NOW)
            general_warning = "Multiple genes shared the same LocusTag or GeneID : %s. The interfeature relationships will not be determined." % (feature_grouping_id)
#            annotation_quality_warnings.append(general_warning)
            sql_cursor.execute("insert into annotation_quality_warnings values(:warning)",(general_warning,))
            for gene_id in gene_features:
                if "quality_warnings" in gene_features[gene_id]:
                    gene_features[gene_id]["quality_warnings"].append(general_warning)
                else:
                    gene_features[gene_id]["quality_warnings"] = [general_warning]    
            for mrna_id in mrna_features:
                if "quality_warnings" in mrna_features[mrna_id]:
                    mrna_features[mrna_id]["quality_warnings"].append(general_warning)
                else:                                                                                                                      
                    mrna_features[mrna_id]["quality_warnings"] = [general_warning]    
            for cds_id in cds_features:
                if "quality_warnings" in cds_features[cds_id]:
                    cds_features[cds_id]["quality_warnings"].append(general_warning)
                else:
                    cds_features[cds_id]["quality_warnings"] = [general_warning]    
        elif num_genes_present == 1:
            #determine interfeature relationships
            #make sure all locations are on the same the contig
            gene_mRNA_list = list() #keep tracks of mRNA that are within the boundaries of the gene.
            gene_CDS_list = list() #keep tracks of CDS that are within the boundaries of the gene.

            contig_check_dict = dict()
            gene_start_boundary = None
            gene_end_boundary = None
            gene_contig = None
            gene_strand = None
            gene_id = features_grouping_dict[feature_grouping_id]["gene"][0]

            if "locations" in gene_features[gene_id]:
                for location in gene_features[gene_id]["locations"]:
                    temp_start_location = location[1]
                    temp_end_location = location[1] + location[3]
                    if location[2] == "-":
                        temp_start_location = location[1] - location[3]
                        temp_end_location = location[1]
                    if gene_start_boundary is None:
                        gene_start_boundary = temp_start_location
                    elif temp_start_location < gene_start_boundary:
                        gene_start_boundary = temp_start_location
                    if gene_end_boundary is None:
                        gene_end_boundary = temp_end_location
                    elif temp_end_location > gene_end_boundary:
                        gene_end_boundary = temp_end_location

                gene_contig = gene_features[gene_id]["locations"][0][0]
                gene_strand = gene_features[gene_id]["locations"][0][2]
                    
            if "mRNA" in features_grouping_dict[feature_grouping_id]:
                for feature_id in features_grouping_dict[feature_grouping_id]["mRNA"]:
                    mRNA_start_boundary = None
                    mRNA_end_boundary = None
                    mRNA_contig = None
                    if "locations" in  mrna_features[feature_id]:
                        for location in mrna_features[feature_id]["locations"]:
                            temp_start_location = location[1] 
                            temp_end_location = location[1] + location[3] 
                            if location[2] == "-": 
                                temp_start_location = location[1] - location[3] 
                                temp_end_location = location[1] 
                            if mRNA_start_boundary is None: 
                                mRNA_start_boundary = temp_start_location
                            elif temp_start_location < mRNA_start_boundary:
                                mRNA_start_boundary = temp_start_location
                            if mRNA_end_boundary is None:
                                mRNA_end_boundary = temp_end_location
                            elif temp_end_location > mRNA_end_boundary:
                                mRNA_end_boundary = temp_end_location
 
                        mRNA_contig = mrna_features[feature_id]["locations"][0][0]
                        mRNA_strand = mrna_features[feature_id]["locations"][0][2]

                        if (mRNA_contig is not None) and \
                           (gene_contig is not None) and \
                           (mRNA_contig == gene_contig) and \
                           (mRNA_strand == gene_strand) :
                            if (mRNA_start_boundary is not None) and \
                               (mRNA_end_boundary is not None) and \
                               (gene_start_boundary is not None) and \
                               (gene_end_boundary is not None):
                                if (mRNA_start_boundary >= gene_start_boundary) and (mRNA_end_boundary <= gene_end_boundary):
                                    needs_to_be_added = True
                                    for mRNA_tuple in gene_mRNA_list:
                                        if feature_id == mRNA_tuple[1]:
                                            needs_to_be_added = False
                                    if needs_to_be_added:
                                        gene_mRNA_list.append(["mRNA",feature_id])
                                    if "mRNA_properties" not in mrna_features[feature_id]:
                                        mrna_features[feature_id]["mRNA_properties"] = dict()
                                    if "parent_gene" not in mrna_features[feature_id]["mRNA_properties"]:
                                        mrna_features[feature_id]["mRNA_properties"]["parent_gene"] = ["gene",gene_id]
                                        if "mRNA_with_gene" not in interfeature_relationship_counts_map:
                                            interfeature_relationship_counts_map["mRNA_with_gene"] = 1
                                        else:
                                            interfeature_relationship_counts_map["mRNA_with_gene"] = interfeature_relationship_counts_map["mRNA_with_gene"] + 1
                                        if "function" not in mrna_features[feature_id] and \
                                           "function" in gene_features[gene_id]:
                                            #inherit function from gene if mRNA has not function
                                            mrna_features[feature_id]["function"] = gene_features[gene_id]["function"]
                                    else:
                                        existing_gene_id = mrna_features[feature_id]["mRNA_properties"]["parent_gene"][1]
                                        if existing_gene_id != gene_id:
                                            general_warning = "mRNA %s ambiguously is associated with two different gene ids (%s and %s), no association can be made" % (feature_id,existing_gene_id,gene_id)
                                            #annotation_quality_warnings.append(general_warning) 
                                            sql_cursor.execute("insert into annotation_quality_warnings values(:warning)",(general_warning,))
                                            del mrna_features[feature_id]["mRNA_properties"]["parent_gene"]
                                            interfeature_relationship_counts_map["gene_with_mRNA"] = interfeature_relationship_counts_map["gene_with_mRNA"] - 1
                                            interfeature_relationship_counts_map["mRNA_with_gene"] = interfeature_relationship_counts_map["mRNA_with_gene"] - 1
                                            del gene_features[existing_gene_id]["gene_properties"]["children_mRNA"] 
                                            gene_mRNA_list = list()
                                            if not mrna_features[feature_id]["mRNA_properties"]:
                                                del mrna_features[feature_id]["mRNA_properties"]
                                            if "quality_warnings" in mrna_features[feature_id]: 
                                                mrna_features[feature_id]["quality_warnings"].append(general_warning) 
                                            else: 
                                                mrna_features[feature_id]["quality_warnings"] = [general_warning] 
                if len(gene_mRNA_list) > 0:
                    if "gene_properties" not in gene_features[gene_id]:
                        gene_features[gene_id]["gene_properties"] = dict()
                    if gene_id not in genes_with_mRNA:
                        temp_dict = dict()
                        for e1 in gene_mRNA_list:
                            temp_dict[e1[1]] = 1
                        new_list = list()
                        for temp_key in temp_dict.keys():
                            new_list.append(["mRNA",temp_key])
                        gene_features[gene_id]["gene_properties"]["children_mRNA"]=new_list 
                        if "gene_with_mRNA" not in interfeature_relationship_counts_map:
                            interfeature_relationship_counts_map["gene_with_mRNA"] = 0
                        interfeature_relationship_counts_map["gene_with_mRNA"] = interfeature_relationship_counts_map["gene_with_mRNA"] + 1
                        genes_with_mRNA[gene_id] = 1
                    elif "children_mRNA" in gene_features[gene_id]["gene_properties"]:
                        temp_dict = dict()
                        for e1 in gene_features[gene_id]["gene_properties"]["children_mRNA"]:
                            temp_dict[e1[1]] = 1
                        for new_child_mRNA in gene_mRNA_list:
                            if new_child_mRNA[1] not in temp_dict:
                                gene_features[gene_id]["gene_properties"]["children_mRNA"].append(new_child_mRNA)


            if "CDS" in features_grouping_dict[feature_grouping_id]: 
                for feature_id in features_grouping_dict[feature_grouping_id]["CDS"]: 
                    CDS_start_boundary = None 
                    CDS_end_boundary = None 
                    CDS_contig = None 
                    if "locations" in cds_features[feature_id]:
                        for location in cds_features[feature_id]["locations"]:
                            temp_start_location = location[1] 
                            temp_end_location = location[1] + location[3] 
                            if location[2] == "-": 
                                temp_start_location = location[1] - location[3] 
                                temp_end_location = location[1] 
                            if CDS_start_boundary is None: 
                                CDS_start_boundary = temp_start_location
                            elif temp_start_location < CDS_start_boundary:
                                CDS_start_boundary = temp_start_location
                            if CDS_end_boundary is None:
                                CDS_end_boundary = temp_end_location
                            elif temp_end_location > CDS_end_boundary:
                                CDS_end_boundary = temp_end_location 
                        CDS_contig = cds_features[feature_id]["locations"][0][0] 
                        CDS_strand = cds_features[feature_id]["locations"][0][2] 

                        if (CDS_contig is not None) and \
                           (gene_contig is not None) and \
                           (CDS_contig == gene_contig) and \
                           (CDS_strand == gene_strand) : 
                            if (CDS_start_boundary is not None) and \
                               (CDS_end_boundary is not None) and \
                               (gene_start_boundary is not None) and \
                               (gene_end_boundary is not None): 
                                if (CDS_start_boundary >= gene_start_boundary) and (CDS_end_boundary <= gene_end_boundary): 
                                    needs_to_be_added = True
                                    for CDS_tuple in gene_CDS_list:
                                        if feature_id == CDS_tuple[1]:
                                            needs_to_be_added = False
                                    if needs_to_be_added:
                                        gene_CDS_list.append(["CDS",feature_id])
                                    if "CDS_properties" not in cds_features[feature_id]: 
                                        cds_features[feature_id]["CDS_properties"] = dict() 
                                    if "parent_gene" not in cds_features[feature_id]["CDS_properties"]:
                                        cds_features[feature_id]["CDS_properties"]["parent_gene"] = ["gene",gene_id] 
                                        if "CDS_with_gene" not in interfeature_relationship_counts_map:
                                            interfeature_relationship_counts_map["CDS_with_gene"] = 1
                                        else:
                                            interfeature_relationship_counts_map["CDS_with_gene"] = interfeature_relationship_counts_map["CDS_with_gene"] + 1
                                        if "function" not in cds_features[feature_id] and \
                                           "function" in gene_features[gene_id]:
                                            #inherit function from gene if CDS has not function
                                            cds_features[feature_id]["function"] = gene_features[gene_id]["function"]
                                    else:
                                        existing_gene_id = cds_features[feature_id]["CDS_properties"]["parent_gene"][1]
                                        if existing_gene_id != gene_id:
                                            general_warning = "CDS %s ambiguously is associated with two different gene ids (%s and %s), no association can be made" % (feature_id,existing_gene_id,gene_id)
                                            #annotation_quality_warnings.append(general_warning) 
                                            sql_cursor.execute("insert into annotation_quality_warnings values(:warning)",(general_warning,))
                                            interfeature_relationship_counts_map["gene_with_CDS"] = interfeature_relationship_counts_map["gene_with_CDS"] - 1
                                            interfeature_relationship_counts_map["CDS_with_gene"] = interfeature_relationship_counts_map["CDS_with_gene"] - 1
                                            del cds_features[feature_id]["CDS_properties"]["parent_gene"]
                                            gene_CDS_list = list()
                                            if not cds_features[feature_id]["CDS_properties"]:
                                                del cds_features[feature_id]["CDS_properties"]
                                            if "quality_warnings" in cds_features[feature_id]: 
                                                cds_features[feature_id]["quality_warnings"].append(general_warning) 
                                            else: 
                                                cds_features[feature_id]["quality_warnings"] = [general_warning] 
                if len(gene_CDS_list) > 0: 
                    if gene_id not in genes_with_CDS:
                        if "gene_properties" not in gene_features[gene_id]: 
                            gene_features[gene_id]["gene_properties"] = dict()
                        temp_dict = dict()
                        for e1 in gene_CDS_list:
                            temp_dict[e1[1]] = 1
                        new_list = list()
                        for temp_key in temp_dict.keys():
                            new_list.append(["CDS",temp_key])
                        gene_features[gene_id]["gene_properties"]["children_CDS"]=new_list 
                        if "gene_with_CDS" not in interfeature_relationship_counts_map:
                            interfeature_relationship_counts_map["gene_with_CDS"] = 0 
                        interfeature_relationship_counts_map["gene_with_CDS"] = interfeature_relationship_counts_map["gene_with_CDS"] + 1
                        genes_with_CDS[gene_id] = 1
                    elif "children_CDS" in gene_features[gene_id]["gene_properties"]:
                        temp_dict = dict()
                        for e1 in gene_features[gene_id]["gene_properties"]["children_CDS"]:
                            temp_dict[e1[1]] = 1
                        for new_child_CDS in gene_CDS_list:
                            if new_child_CDS[1] not in temp_dict:
                                gene_features[gene_id]["gene_properties"]["children_CDS"].append(new_child_CDS)


        #########################        
        #CDS to mRNA interfeature relationships
        #########################
        if num_mrna_present > 0 and num_cds_present > 0:
            #Means both CDS and mRNA present in this grouping
            #try to determine how if they relate to one another.
            CDS_mRNA_match_dict = dict() #key is CDS, value is dict of mRNA sequences it matches as key. Value is # of bases larger the mRNA is 
            CDS_length_dict = dict()

            for mRNA_feature_id in features_grouping_dict[feature_grouping_id]["mRNA"]: 
                mRNA_start_boundary = None 
                mRNA_end_boundary = None 
                mRNA_contig = None 
                if "locations" in mrna_features[mRNA_feature_id]: 
                    for location in mrna_features[mRNA_feature_id]["locations"]:
                        temp_start_location = location[1] 
                        temp_end_location = location[1] + location[3] 
                        if location[2] == "-": 
                            temp_start_location = location[1] - location[3] 
                            temp_end_location = location[1] 
                        if mRNA_start_boundary is None: 
                            mRNA_start_boundary = temp_start_location
                        elif temp_start_location < mRNA_start_boundary:
                            mRNA_start_boundary = temp_start_location
                        if mRNA_end_boundary is None:
                            mRNA_end_boundary = temp_end_location
                        elif temp_end_location > mRNA_end_boundary:
                            mRNA_end_boundary = temp_end_location

                    mRNA_contig = mrna_features[mRNA_feature_id]["locations"][0][0] 
                    mRNA_strand = mrna_features[mRNA_feature_id]["locations"][0][2] 

                    if "dna_sequence" in mrna_features[mRNA_feature_id]:
                        mRNA_sequence = mrna_features[mRNA_feature_id]["dna_sequence"]
                        for CDS_feature_id in features_grouping_dict[feature_grouping_id]["CDS"]:
                            CDS_start_boundary = None 
                            CDS_end_boundary = None 
                            CDS_contig = None 

                            if "locations" in cds_features[CDS_feature_id]: 
                                for location in cds_features[CDS_feature_id]["locations"]:
                                    temp_start_location = location[1] 
                                    temp_end_location = location[1] + location[3] 
                                    if location[2] == "-": 
                                        temp_start_location = location[1] - location[3] 
                                        temp_end_location = location[1] 
                                    if CDS_start_boundary is None: 
                                        CDS_start_boundary = temp_start_location
                                    elif temp_start_location < CDS_start_boundary:
                                        CDS_start_boundary = temp_start_location
                                    if CDS_end_boundary is None:
                                        CDS_end_boundary = temp_end_location
                                    elif temp_end_location > CDS_end_boundary:
                                        CDS_end_boundary = temp_end_location 

                                CDS_contig = cds_features[CDS_feature_id]["locations"][0][0] 
                                CDS_strand = cds_features[CDS_feature_id]["locations"][0][2] 

                                if (CDS_contig is not None) and (mRNA_contig is not None) and \
                                   (CDS_contig == mRNA_contig) and (CDS_strand == mRNA_strand) : 
                                    if (CDS_start_boundary is not None) and \
                                       (CDS_end_boundary is not None) and \
                                       (mRNA_start_boundary is not None) and \
                                       (mRNA_end_boundary is not None): 
                                        if (CDS_start_boundary >= mRNA_start_boundary) and \
                                           (CDS_end_boundary <= mRNA_end_boundary):

                                            if "dna_sequence" in cds_features[CDS_feature_id]:
                                                CDS_sequence = cds_features[CDS_feature_id]["dna_sequence"]
                                                if CDS_sequence in mRNA_sequence:
                                                    if CDS_feature_id not in CDS_mRNA_match_dict :
                                                        CDS_mRNA_match_dict[CDS_feature_id] = dict()
                                                    diff_length = len(mRNA_sequence) - len(CDS_sequence)
                                                    CDS_mRNA_match_dict[CDS_feature_id][mRNA_feature_id] = diff_length
                                                    CDS_length_dict[CDS_feature_id] =(len(CDS_sequence))
            
            CDS_to_mRNA_pairings_made = dict()
            mRNA_to_CDS_pairings_made = dict()
            pairings_are_ambiguous = False
            #GO THROUGH THE CDS LIST FROM BIGGEST TO SMALLEST.  MOST LIKELY TO HAVE ONE HIT AS LARGEST CAN ONLY FIT IN SMALLER NUMBER OF MRNAS
            for CDS_feature_id in sorted(CDS_length_dict, key=CDS_length_dict.get, reverse=True):
                mRNA_hit_tuples = sorted(CDS_mRNA_match_dict[CDS_feature_id].items(), key=lambda x: x[1])

                #This gives you just the keys.
                mRNA_hits = list()
                for mRNA_hit_tuple in mRNA_hit_tuples:
                    mRNA_hits.append(mRNA_hit_tuple[0])
#                mRNA_hits = [mRNA_tuple[0] for mRNA_hit_tuples]
#                print "mRNA_hits: " + str(mRNA_hits)

                if len(mRNA_hits) == 1:
                    #Only one hit so only pairing to be made
#                    CDS_to_mRNA_pairings_made[CDS_feature_id] = CDS_mRNA_match_dict[CDS_feature_id][mRNA_hits[0]]
#                    mRNA_to_CDS_pairings_made[CDS_mRNA_match_dict[CDS_feature_id][mRNA_hits[0]]] = CDS_feature_id
                    CDS_to_mRNA_pairings_made[CDS_feature_id] = mRNA_hits[0]
                    mRNA_to_CDS_pairings_made[mRNA_hits[0]] = CDS_feature_id

                elif len(mRNA_hits) > 1:
                    #If more than one hit try the one with the smallest differential in size.  If it has a match already it is ambiguous.
                    #Note importnatly that CDS list sorted biggest smallest.  Then mRNA hits smallest size difference to the biggest.
                    #insures best chances matching splice variants that are a subset of the sequence of a larger splice variant.
                    mRNA_feature_id = mRNA_hits[0]
                    if mRNA_feature_id in mRNA_to_CDS_pairings_made:
                        #Means that mRNA has been paired with a CDS already the 1 to 1 relationship is ambiguous
                        CDS_warning = "This CDS %s can not be definitively matched to just one mRNA; it hits %s" % \
                                      (CDS_feature_id,",".join(mRNA_hits))
                        #annotation_quality_warnings.append(CDS_warning)
                        sql_cursor.execute("insert into annotation_quality_warnings values(:warning)",(CDS_warning,))
                        mRNA_warning = "This mRNA %s can not be definitively matched to just one CDS; it hits %s and %s" % \
                                       (mRNA_feature_id,CDS_feature_id,mRNA_to_CDS_pairings_made[mRNA_feature_id])
                        #annotation_quality_warnings.append(mRNA_warning)
                        sql_cursor.execute("insert into annotation_quality_warnings values(:warning)",(mRNA_warning,))
                        if "quality_warnings" in cds_features[CDS_feature_id]:
                            cds_features[CDS_feature_id]["quality_warnings"].append(CDS_warning)
                        else: 
                            cds_features[CDS_feature_id]["quality_warnings"]=[CDS_warning]

                        if "quality_warnings" in mrna_features[mRNA_feature_id]:
                            mrna_features[mRNA_feature_id]["quality_warnings"].append(mRNA_warning)
                        else: 
                            mrna_features[mRNA_feature_id]["quality_warnings"]=[mRNA_warning]
                        
                        pairings_are_ambiguous = True
                    else :
                        CDS_to_mRNA_pairings_made[CDS_feature_id] = mRNA_feature_id
                        mRNA_to_CDS_pairings_made[mRNA_feature_id] = CDS_feature_id 
            if pairings_are_ambiguous == False:
                #Add the information to the CDS and mRNA properties
                for CDS_feature_id in CDS_to_mRNA_pairings_made:
                    if "CDS_properties" not in cds_features[CDS_feature_id]: 
                        cds_features[CDS_feature_id]["CDS_properties"] = dict() 
                    if "asssociated_mRNA" in cds_features[CDS_feature_id]["CDS_properties"]:
                        existing_mRNA_id = cds_features[CDS_feature_id]["CDS_properties"]["associated_mRNA"][1]
                        if CDS_to_mRNA_pairings_made[CDS_feature_id] != existing_mRNA_id:
                            #REMOVE THE OLD ONE ASSOCIATION, POTENTIALLY REMOVE THE PROPERTIES, ADD A WARNING
                            general_warning = "CDS %s ambiguously is associated with two different mRNA ids (%s and %s), no association can be made" % (feature_id,existing_mRNA_id,CDS_to_mRNA_pairings_made[CDS_feature_id])
                            #annotation_quality_warnings.append(general_warning)
                            sql_cursor.execute("insert into annotation_quality_warnings values(:warning)",(general_warning,))
                            del cds_features[CDS_feature_id]["CDS_properties"]["associated_mRNA"]

                            if not cds_features[CDS_feature_id]["CDS_properties"]:
                                del cds_features[CDS_feature_id]["CDS_properties"]
                                if "quality_warnings" in cds_features[CDS_feature_id]:
                                    cds_features[CDS_feature_id]["quality_warnings"].append(general_warning)
                                else: 
                                    cds_features[CDS_feature_id]["quality_warnings"] = [general_warning]
                    else:
                        cds_features[CDS_feature_id]["CDS_properties"]["associated_mRNA"] \
                            = ["mRNA",CDS_to_mRNA_pairings_made[CDS_feature_id]] 
                for mRNA_feature_id in mRNA_to_CDS_pairings_made:
#                    print " mRNA_to_CDS_pairings_made : \n" + str( mRNA_to_CDS_pairings_made)
                    if "mRNA_properties" not in mrna_features[mRNA_feature_id]: 
                        mrna_features[mRNA_feature_id]["mRNA_properties"] = dict() 
                    if "asssociated_CDS" in mrna_features[mRNA_feature_id]["mRNA_properties"]:
                        existing_CDS_id = mrna_features[mRNA_feature_id]["mRNA_properties"]["associated_CDS"][1]
                        if mRNA_to_CDS_pairings_made[mRNA_feature_id] != existing_CDS_id:
                            #REMOVE THE OLD ONE ASSOCIATION, POTENTIALLY REMOVE THE PROPERTIES, ADD A WARNING
                            general_warning = "mRNA %s ambiguously is associated with two different CDS ids (%s and %s), no association can be made" % (feature_id,existing_CDS_id,mRNA_to_CDS_pairings_made[mRNA_feature_id])
                            #annotation_quality_warnings.append(general_warning)
                            sql_cursor.execute("insert into annotation_quality_warnings values(:warning)",(general_warning,))
                            del mrna_features[mRNA_feature_id]["mRNA_properties"]["associated_CDS"]

                            if not mrna_features[mRNA_feature_id]["mRNA_properties"]:
                                del mrna_features[mRNA_feature_id]["mRNA_properties"]
                                if "quality_warnings" in mrna_features[mRNA_feature_id]:
                                    mrna_features[mRNA_feature_id]["quality_warnings"].append(general_warning)
                                else: 
                                    mrna_features[mRNA_feature_id]["quality_warnings"] = [general_warning]
                    else:
                        mrna_features[mRNA_feature_id]["mRNA_properties"]["associated_CDS"] \
                            = ["CDS",mRNA_to_CDS_pairings_made[mRNA_feature_id]] 


        running_grouping_elements_count += (num_cds_present + num_mrna_present + num_genes_present)

        if ((num_cds_present < 1) or (num_mrna_present < 1) or (num_genes_present < 1)):
            groupings_without_three_levels += 1
            if num_cds_present != num_mrna_present:
                inner_unequal_cds_mrna_count += 1

        if num_cds_present != num_mrna_present:
            unequal_cds_mrna_count += 1

        #NEED TO RESAVE ALL THE FEATURES IN THE GROUPINGS BACK INTO SQLLITE 
        for cds_id in cds_features:
            pdata = cPickle.dumps(cds_features[cds_id], cPickle.HIGHEST_PROTOCOL) 
            sql_cursor.execute("update features set feature_data = ? where feature_id = ?", (sqlite3.Binary(pdata),cds_id,)) 
        for mrna_id in mrna_features:
            pdata = cPickle.dumps(mrna_features[mrna_id], cPickle.HIGHEST_PROTOCOL) 
            sql_cursor.execute("update features set feature_data = ? where feature_id = ?", (sqlite3.Binary(pdata),mrna_id,)) 
        for cds_id in cds_features:
            pdata = cPickle.dumps(gene_features[gene_id], cPickle.HIGHEST_PROTOCOL) 
            sql_cursor.execute("update features set feature_data = ? where feature_id = ?", (sqlite3.Binary(pdata),gene_id,)) 

    print "Total Groupings length : " + str(len(features_grouping_dict))
    print "Running group elements count : " + str(running_grouping_elements_count)
    print "Grouping without three levels : " + str(groupings_without_three_levels)
    print "Number of unequal cds mrna : " + str(unequal_cds_mrna_count)
    print "Number of inner unequal cds mrna : " + str(inner_unequal_cds_mrna_count)

#    sys.exit(1)

    #build up protein container
    #Save protein container.
    protein_container_object_name = "%s_protein_container" % (core_genome_name)
    protein_reference = None
    if len(protein_container_dict) > 0: 
        protein_container = dict()
        protein_container_provenance = [{"script": __file__, "script_ver": "0.1", "description": "proteins from upload from %s " % (source_name)}]
        #Provencance has a 1 MB limit.  We may want to add more like the accessions, but to be safe for now not doing that.
        #provenance_description = "proteins from upload from %s includes accession(s) : " % (source_name,",".join(locus_name_order))
        protein_container_provenance = [{"script": __file__, "script_ver": "0.1", "description": "proteins from upload from %s" % (source_name)}]

#        protein_container_not_saved = True 
        protein_container['protein_container_id'] = protein_container_object_name 
        protein_container['name'] = protein_container_object_name
        protein_container['notes'] = "proteins from upload from %s" % (source_name)

        protein_reference = "%s/%s" % (workspace_name, protein_container_object_name)

        protein_container_dict = dict()
        sql_cursor.execute("select protein_id, protein_data from proteins")
        for row in sql_cursor: 
            protein_container_dict[row[0]] =  cPickle.loads(str(row[1]))
        
        feature_type_counts['protein'] = len(protein_container_dict)
        protein_container['proteins'] = protein_container_dict
#        while protein_container_not_saved:
#            try: 
#        print "PROTEIN CONTAINER : \n\n\n\n" + str(protein_container)

        logger.info("Attempting Protein Container save for %s" % (protein_container_object_name))  
        protein_container_info =  ws_client.save_objects({"workspace": workspace_name,
                                                          "objects":[ { "type":"KBaseGenomeAnnotations.ProteinContainer",
                                                                        "data":protein_container,
                                                                        "name": protein_container_object_name,
                                                                        "hidden":1,
                                                                        "provenance":protein_container_provenance}]})
        logger.info("Protein Container saved for %s" % (protein_container_object_name))  
#                protein_container_not_saved = False 
#            except biokbase.workspace.client.ServerError as err:
#                #KEEPS GOING FOR NOW.  DO WE WANT TO HAVE A LIMIT?
#                raise 


    else:
        raise Exception("No CDS annotations exist in this Genbank file.  This appears not to be a genome.  If this is just an assembly, you should upload it as an assembly# using a fasta file.")


    counts_map = dict() #dict of feature type and number of occurrences.

    #Go through each feature type and build up the feature objects for the feature containers
    #Save feature containers
    sql_cursor.execute("select distinct feature_type from features")
    feature_type_list = list()
    for row in sql_cursor:
        feature_type_list.append(row[0])

    for feature_type in feature_type_list:
        print "TYPE IN : " + feature_type

        sanitized_feature_type = re.sub(r'\W+', '', feature_type) 
        feature_container_object_name = "%s_feature_container_%s" % (core_genome_name,sanitized_feature_type)
        feature_container_object_ref = "%s/%s" % (workspace_name,feature_container_object_name)

        features_dict = dict()
        feature_container = dict()
        feature_container['features'] = dict()

        #Do size check of the features
        sql_cursor.execute("select sum(length(feature_data)) from features where feature_type = ?", (feature_type,))
        for row in sql_cursor:
            data_length = row[0]

        if data_length < 900000000:
            #Size is probably ok Try the save
            #Retrieve the features from the sqllite DB
            sql_cursor.execute("select feature_id, feature_data from features where feature_type = ? ", (feature_type,))

            for row in sql_cursor: 
                feature_id = row[0]
                feature_data = cPickle.loads(str(row[1])) 
                feature_container['features'][feature_id] = feature_data

            #Build up container object
            feature_container['feature_container_id']= feature_container_object_name
            feature_container['name']= feature_container_object_name
            feature_container['type']= feature_type
            feature_container['assembly_ref'] = assembly_reference

            feature_container_references[feature_type] = feature_container_object_ref

            #Provenance has a 1 MB limit.  We may want to add more like the accessions, but to be safe for now not doing that.
            #provenance_description = "features from upload from %s includes accession(s) : " % (source_name,",".join(locus_name_order))
            feature_container_provenance = [{"script": __file__, "script_ver": "0.1", "description": "features from upload from %s" % (source_name)}]
            logger.info("Attempting save of Feature Container %s" % (feature_container_object_name)) 

            #determine mRNA to CDS relationship counts
            if feature_type == "CDS":
                CDS_to_mRNA_count = 0 
                for feature in feature_container['features']:
                    if "CDS_properties" in feature_container['features'][feature]:
                        if "associated_mRNA" in feature_container['features'][feature]["CDS_properties"]:
                            CDS_to_mRNA_count += 1 
                interfeature_relationship_counts_map["CDS_with_mRNA"] = CDS_to_mRNA_count
 
            if feature_type == "mRNA":
                mRNA_to_CDS_count = 0 
                for feature in feature_container['features']:
                    if "mRNA_properties" in feature_container['features'][feature]:
                        if "associated_CDS" in feature_container['features'][feature]["mRNA_properties"]:
                            mRNA_to_CDS_count += 1 
                interfeature_relationship_counts_map["mRNA_with_CDS"] = mRNA_to_CDS_count

            counts_map[feature_type] = len(feature_container['features'])
            feature_container_info =  ws_client.save_objects({"workspace":workspace_name,
                                                              "objects":[ { "type":"KBaseGenomeAnnotations.FeatureContainer",
                                                                            "data":feature_container,
                                                                            "name": feature_container_object_name,
                                                                            "hidden":1,
                                                                            "provenance":feature_container_provenance}]}) 
            logger.info("Feature Container saved for %s" % (feature_container_object_name)) 
        else:
            #Feature container too large
            #If core type Fail
            if feature_type in ["gene", "mRNA", "CDS"]:
                raise Exception("This genome annotation can not be saved due to at least one of the core feature types (gene, CDS, mRNA) being too large for the workspace")
            #Else do not save the feature container (add waring)
            else:
                temp_warning = "Feature type {} will not be made because the resulting object will be too large for the workspace.".format(feature_type)
                #annotation_quality_warnings.append(temp_warning)
                sql_cursor.execute("insert into annotation_quality_warnings values(:warning)",(temp_warning,))
                alias_list = feature_lookup_dict.keys()
                for alias in alias_list:
                    f_counter = 0
#                    alias_tuple_list = feature_lookup_dict[alias]
                    for temp_fc_ref, temp_fc_id in feature_lookup_dict[alias]:
                        if feature_type == reverse_feature_container_ref_lookup[temp_fc_ref]:
                            #HOW TO REMOVE TUPLE FROM LIST IN PLACE?
                            del( feature_lookup_dict[alias][f_counter])
                        else:
                            # important because the positions of all values will be decremented on a delete
                            # so only increment if you did not delete                   
                            f_counter += 1
                    if len(feature_lookup_dict[alias]) == 0:
                        #Need to remove the alias.
                        del( feature_lookup_dict[alias]) 

    #MAKE THE BAREBONES ANNOTATION QUALITY OBJECT:
    #LIST OF WARNINGS TO PUT INTO THE AnnotationQualityObject.
    annotation_quality_warnings = list()
    annotation_metadata_warnings = list()

    #Retrieve the warnings from the sqllite DB                                                                                                                                                                                       
    sql_cursor.execute("select warning from annotation_quality_warnings")
    for row in sql_cursor: 
        annotation_quality_warnings.append(row[0]) 

    sql_cursor.execute("select warning from annotation_metadata_warnings")
    for row in sql_cursor: 
        annotation_metadata_warnings.append(row[0]) 

    annotation_quality_object = dict()
    annotation_quality_object["metadata_completeness"] = 0
    annotation_quality_object["metadata_completeness_warnings"] = annotation_metadata_warnings
    annotation_quality_object["data_quality"] = 0
    annotation_quality_object["data_quality_warnings"] = annotation_quality_warnings
    annotation_quality_object["feature_types_present"] = len(counts_map) 
    annotation_quality_object["evidence_supported"] = 0

    annotation_quality_object_name = "%s_annontation_quality" % (core_genome_name)
    annotation_quality_reference =  "%s/%s" % (workspace_name,annotation_quality_object_name)
    annotation_quality_provenance = [{"script": __file__, "script_ver": "0.1", "description": "annotation quality from upload from %s" % (source_name)}]

    annotation_quality_object_info =  ws_client.save_objects({"workspace":workspace_name, 
                                                              "objects":[ { "type":"KBaseGenomeAnnotations.AnnotationQuality",
                                                                            "data": annotation_quality_object,
                                                                            "name": annotation_quality_object_name,
                                                                            "hidden":1, 
                                                                            "provenance":annotation_quality_provenance}]}) 
    logger.info("Annotation Quality saved for %s" % (annotation_quality_object_name)) 

    #Save genome annotation
    #Then Finally store the GenomeAnnotation.                                                                            

    shock_id = None
    handle_id = None
    if shock_id is None:
        shock_info = script_utils.upload_file_to_shock(logger, shock_service_url, input_file_name, token=token)
        shock_id = shock_info["id"]
        handles = script_utils.getHandles(logger, shock_service_url, handle_service_url, [shock_id], [handle_id], token)   
        handle_id = handles[0]

    genome_annotation['genbank_handle_ref'] = handle_id
    genome_annotation['feature_lookup'] = feature_lookup_dict
    genome_annotation['protein_container_ref'] = protein_reference
    genome_annotation['feature_container_references'] = feature_container_references 
    genome_annotation['counts_map'] = counts_map
    genome_annotation_provenance = [{"script": __file__, "script_ver": "0.1", "description": "features from upload from %s" % (source_name)}]

#    genome_annotation_not_saved = True
    genome_annotation_object_name = core_genome_name 
    genome_annotation['type'] = type 
    if type == "Reference":
        genome_annotation['reference_annotation'] = 1
    else:
        genome_annotation['reference_annotation'] = 0
    genome_annotation['taxon_ref'] = taxon_id
    genome_annotation['display_sc_name'] = display_sc_name
    genome_annotation['original_source_file_name'] = source_file_name
    genome_annotation['assembly_ref'] =  assembly_reference 
    genome_annotation['genome_annotation_id'] = genome_annotation_object_name
    genome_annotation['external_source'] = source_name
    genome_annotation['external_source_id'] = ",".join(locus_name_order)
    genome_annotation['external_source_origination_date'] = genbank_time_string
    genome_annotation['interfeature_relationship_counts_map'] = interfeature_relationship_counts_map
    genome_annotation['alias_source_counts_map'] = alias_source_counts_map
    genome_annotation['annotation_quality_ref'] = annotation_quality_reference
    if release is not None:
        genome_annotation['release'] = release

#    print "Genome Annotation id %s" % (genome_annotation['genome_annotation_id'])
 
    logger.info("Attempting Genome Annotation save for %s" % (genome_annotation_object_name))
#    while genome_annotation_not_saved:
#        try:
    genome_annotation_info =  ws_client.save_objects({"workspace":workspace_name,
                                                      "objects":[ { "type":"KBaseGenomeAnnotations.GenomeAnnotation",
                                                                    "data":genome_annotation,
                                                                    "name": genome_annotation_object_name,
                                                                    "provenance":genome_annotation_provenance}]}) 
#            genome_annotation_not_saved = False 
    logger.info("Genome Annotation saved for %s" % (genome_annotation_object_name))
#        except biokbase.workspace.client.ServerError as err: 
#            raise 

    if not make_sql_in_memory:
        os.remove(db_name) 

    logger.info("Conversions completed.")

    return genome_annotation_object_name

# called only if script is run from command line
if __name__ == "__main__":
    script_details = script_utils.parse_docs(upload_genome.__doc__)    

    import argparse

    parser = argparse.ArgumentParser(prog=__file__, 
                                     description=script_details["Description"],
                                     epilog=script_details["Authors"])
                                     
    parser.add_argument('--shock_service_url', 
                        help=script_details["Args"]["shock_service_url"],
                        action='store', type=str, nargs='?', required=True)
    parser.add_argument('--handle_service_url', 
#                        help=script_details["Args"]["handle_service_url"], 
                        action='store', type=str, nargs='?', default=None, required=True)
#    parser.add_argument('--input_file_name', 
#                        help="genbank file", 
#                        nargs='?', required=True)
    parser.add_argument('--workspace_name', nargs='?', help='workspace name to populate', required=True)
    parser.add_argument('--taxon_wsname', nargs='?', help='workspace name with taxon in it, assumes the same workspace_service_url', required=False, default='ReferenceTaxons')
#    parser.add_argument('--taxon_names_file', nargs='?', help='file with scientific name to taxon id mapping information in it.', required=False, default="/homes/oakland/jkbaumohl/Genome_Spec_files/Taxonomy/names.dmp")
    parser.add_argument('--taxon_reference', nargs='?', help='ONLY NEEDED IF PERSON IS DOING A CUSTOM TAXON NOT REPRESENTED IN THE NCBI TAXONOMY TREE', required=False)
    parser.add_argument('--workspace_service_url', action='store', type=str, nargs='?', required=True) 

    parser.add_argument('--object_name', 
                        help="genbank file", 
                        nargs='?', required=False)
    parser.add_argument('--exclude_feature_types', type=str, nargs='*', required=False,
                        help='which feature types to exclude.  feature type "source" is always excluded.  Ensembl should exclude "misc_feature"') 
#    parser.add_argument('--fasta_file_directory', 
#                        help="fasta_dile_directory", 
#                        nargs='?', required=False) 
    parser.add_argument('--source', 
                        help="data source : examples Refseq, Genbank, Pythozyme, Gramene, etc", 
                        nargs='?', required=False, default="Genbank") 
    parser.add_argument('--type', 
                        help="data source : examples Reference, Representative, User Upload", 
                        nargs='?', required=False, default="User upload") 
    parser.add_argument('--release', 
                        help="Release or version of the data.  Example Ensembl release 30", 
                        nargs='?', required=False) 
#    parser.add_argument('--genome_list_file', action='store', type=str, nargs='?', required=True) 

    parser.add_argument('--input_directory', 
                        help="directory the genbank file is in", 
                        action='store', type=str, nargs='?', required=True)
    parser.add_argument('--no_convert',
                        help="Dont convert", action='store_true',
                        dest='no_convert_to_old_type')
#    parser.add_argument('--output_file_name',
#                        help=script_details["Args"]["output_file_name"],
#                        action='store', type=str, nargs='?', default=None, required=False)
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
        obj_name = upload_genome(shock_service_url = args.shock_service_url,
                      handle_service_url = args.handle_service_url, 
                      #                  output_file_name = args.output_file_name, 
                      #                      input_file_name = args.input_file_name, 
                      input_directory = args.input_directory, 
                      #                  shock_id = args.shock_id, 
                      #                  handle_id = args.handle_id,
                      #                  input_mapping = args.input_mapping,
                      workspace_name = args.workspace_name,
                      workspace_service_url = args.workspace_service_url,
                      taxon_wsname = args.taxon_wsname,
                      exclude_feature_types = args.exclude_feature_types,
#                      taxon_names_file = args.taxon_names_file,
                      taxon_reference = args.taxon_reference,
                      core_genome_name = args.object_name,
                      source = args.source,
                      release = args.release,
                      type = args.type,
                      #                      genome_list_file = args.genome_list_file,
                      logger = logger)
    except Exception, e:
        logger.exception(e)
        sys.exit(1)

    if args.no_convert_to_old_type:
        logger.info('Conversion to legacy types skipped by request')
    else:
        from doekbase.data_api.converters import genome as cvt
        script_utils.stderrlogger(cvt._log.name) # capture converter logs as well
        logger.info('Converting to legacy type, object={}'.format(obj_name))
        try:
            cvt.convert_genome(shock_url=args.shock_service_url,
                               handle_url=args.handle_service_url,
                               ws_url=args.workspace_service_url,
                               obj_name=obj_name,
                               ws_name=args.workspace_name)
        except cvt.ConvertOldTypeException as e:
            logger.exception(e)
            sys.exit(2)

    sys.exit(0)


