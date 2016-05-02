#!/usr/bin/env python

#GFF3 format
#http://www.sequenceontology.org/gff3.shtml
#http://gmod.org/wiki/GFF3

# Standard imports
import sys,os

# 3rd party imports
import simplejson

# KBase imports
import biokbase.Transform.script_utils as script_utils
import biokbase.Transform.TextFileDecoder as TextFileDecoder
import trns_transform_FASTA_DNA_Assembly_to_KBaseGenomeAnnotations_Assembly as assembly
logger = script_utils.stderrlogger(__file__)

if __name__ == "__main__":
    input_directory = "/homes/seaver/Software/KBase_Repos/transform/t/"
    tax_id = "Athaliana"
    genome_type = "Reference"
    source_name = "Phytozome"
    core_genome_name = "%s_%s" % (tax_id,source_name) 
    workspace_name = "GFF_Test"

    logger.info("Uploading Assembly")
    assembly_reference = "%s/%s_assembly" % (workspace_name,core_genome_name)
#    try:
#        fasta_working_dir = str(os.getcwd()) + "/temp_fasta_file_dir"

#        print "HANDLE SERVICE URL " + handle_service_url
#        assembly.upload_assembly(shock_service_url = shock_service_url,
#                                 handle_service_url = handle_service_url,
#                                 input_directory = fasta_working_dir,
                                 #                  shock_id = args.shock_id,
                                 #                  handle_id = args.handle_id,
                                 #                  input_mapping = args.input_mapping, 
#                                 workspace_name = workspace_name,
#                                 workspace_service_url = workspace_service_url,
#                                 taxon_reference = taxon_id,
#                                 assembly_name = "%s_assembly" % (core_genome_name),
#                                 source = source_name,
#                                 contig_information_dict = contig_information_dict,
#                                 date_string = genbank_time_string,
#                                 logger = logger)
#        shutil.rmtree(fasta_working_dir)
#    except Exception, e: 
#        logger.exception(e) 
#        sys.exit(1) 

    logger.info("Assembly Uploaded")

    logger.info("Scanning for Genbank Format files.") 
 
    valid_extensions = [".gff",".gff3"] 
 
    files = os.listdir(os.path.abspath(input_directory)) 
    gff_files = [x for x in files if os.path.splitext(x)[-1] in valid_extensions] 
 
    if (len(gff_files) == 0): 
        raise Exception("The input directory does not have one of the following extensions %s." % (",".join(valid_extensions))) 
  
    logger.info("Found {0}".format(str(gff_files))) 
 
    input_file_name = os.path.join(input_directory,gff_files[0]) 

    if not os.path.isfile(input_file_name):
        logger.warning("{0} is not a recognizable file".format(input_file_name))

    if len(gff_files) > 1: 
        # TODO if multiple files - CONCATENATE FILES HERE (sort by name)? OR Change how the byte coordinates work.
        logger.warning("Not sure how to handle multiple GFF files in this context. Using {0}".format(input_file_name))

    print "INPUT FILE NAME :" + input_file_name + ":"

    header = []
    contigs = {}
    contig_list = []

    gff_file_handle = TextFileDecoder.open_textdecoder(input_file_name, 'ISO-8859-1')
    current_line = gff_file_handle.readline()
    while ( current_line != '' ):
        current_line=current_line.strip()
        
        if(current_line.startswith("##")):
            header.append(current_line)
        else:
            seqid, source, type, start, end, score, strand, phase, attributes = current_line.split('\t')
            if(seqid not in contigs):
                contigs[seqid]={'id':seqid,'source':source,'features':[]}
                contig_list.append(seqid)

            feature = {'type':type,'start':start,'end':end,'score':score,'strand':strand,'phase':phase,'attributes':attributes}
            contigs[seqid]['features'].append(feature)

        current_line = gff_file_handle.readline()

    genome_annotation = dict()

#    print "FASTA FILE Name :"+ fasta_file_name + ":"

    features_type_containers_dict = dict()
    features_type_id_counter_dict = dict()
    features_container_references = dict()
    features_grouping_dict = dict() 
    features_type_counts = dict()
 
    protein_container_dict = dict()
    protein_id_counter = 1;

    for contig in contig_list:
    ##################################################################################################
    #FEATURE ANNOTATION PORTION - Build up datastructures to be able to build feature containers.
    ##################################################################################################
        print contig,len(contigs[contig]['features'])

        for feature in contigs[contig]['features']:
            #feature_object["type"] = feature_type
            #feature_object["feature_id"] = feature_id
            #feature_object["locations"]=locations
            #feature_object["dna_sequence_length"] = dna_sequence_length
            #feature_object["dna_sequence"] = dna_sequence
            #feature_object["md5"] = hashlib.md5(dna_sequence).hexdigest() 

            #feature_object["function"] = value
            #feature_object["trans_splicing"] = 1
            #feature_object["additional_properties"] = additional_properties
            #feature_object["notes"] = notes
            #feature_object["inference"] = inference
            #feature_object["aliases"] = alias_dict
            #feature_object["quality_warnings"] = quality_warnings
            #features_type_containers_dict[feature_type][feature_id] = feature_object

            #!feature_object["gene"] = value 
            #!feature_object["locus_tag"] = value 
            #!feature_object["feature_specific_id"] = value
            #!feature_object["translation"] = value

            feature_object = dict()
            feature_object["type"]=feature["type"]
            if feature['type'] not in features_type_containers_dict:
                features_type_containers_dict[feature['type']] = dict()

            if feature['type'] not in features_type_id_counter_dict:
                features_type_id_counter_dict[feature['type']] = 1;
                feature_id = "%s_%s" % (feature['type'],str(1)) 
            else: 
                features_type_id_counter_dict[feature['type']] += 1; 
                feature_id = "%s_%s" % (feature['type'],str(features_type_id_counter_dict[feature['type']]))

            feature_object["feature_id"]=feature_id
            feature_object["dna_sequence"]=""
            feature_object["dna_sequence_length"]=0
            feature_object["md5"]=""
            feature_object["locations"]=list()
            feature_object["quality_warnings"]=list()

            features_type_containers_dict[feature["type"]][feature_id] = feature_object

            #############################
            #build up protein object
            #############################
            if feature['type'] == 'CDS' and "dna_sequence" in feature_object:

                #Build up the protein object for the protein container
                protein_object = dict()
                protein_id = "protein_%s" % (str(protein_id_counter))
                protein_id_counter += 1
                protein_object["protein_id"] = protein_id
                protein_object["amino_acid_sequence"] = ""

                #Translate feature_object["dna_sequence"]
                #Add it to feature_object["translation"]
                #Add it to protein_object["amino_acid_sequence"]
                #Make sure its upper class
                #from Bio.Seq import Seq
                #from Bio.Alphabet import IUPAC, generic_dna
                #if "dna_sequence" in feature_object:
                #    coding_dna = Seq(feature_object["dna_sequence"], generic_dna)
                #    aa_seq = coding_dna.translate()
                #    protein_object["amino_acid_sequence"] = str(aa_seq[0:].upper())

                if "function" in feature_object:
                    protein_object["function"] = feature_object["function"]

                protein_object["aliases"]=dict()
                if "aliases" in feature_object:
                    protein_object["aliases"] = feature_object["aliases"]

                protein_object["md5"] = "" #hashlib.md5(protein_object["amino_acid_sequence"]).hexdigest()
                protein_container_dict[protein_object["protein_id"]] = protein_object
                protein_container_object_name = "%s_protein_container" % (core_genome_name)

                if "CDS_properties" not in features_type_containers_dict["CDS"][feature_id]: 
                    features_type_containers_dict["CDS"][feature_id]["CDS_properties"] = dict() 
                    protein_ref = "%s/%s" % (workspace_name,protein_container_object_name)
                    features_type_containers_dict["CDS"][feature_id]["CDS_properties"]["codes_for_protein_ref"] = [protein_ref,protein_id]

    counts_map = dict() #dict of feature type and number of occurrences.
    if len(features_type_containers_dict) > 0:
        for feature_type in features_type_containers_dict:

            feature_container = dict()

            feature_container_object_name = "%s_feature_container_%s" % (core_genome_name,feature_type)
            feature_container_object_ref = "%s/%s" % (workspace_name,feature_container_object_name)
            features_container_references[feature_type] = feature_container_object_ref 
            feature_container['feature_container_id']= feature_container_object_name
            feature_container['name']= feature_container_object_name
            feature_container['type']= feature_type
            feature_container['features'] = features_type_containers_dict[feature_type]
            feature_container['assembly_ref'] = assembly_reference

            features_type_counts[feature_type] = len(features_type_containers_dict[feature_type])
            counts_map[feature_type] = len(features_type_containers_dict[feature_type])

            #Provenance has a 1 MB limit.  We may want to add more like the accessions, but to be safe for now not doing that.
            #provenance_description = "features from upload from %s includes accession(s) : " % (source_name,",".join(locus_name_order))
            feature_container_provenance = [{"script": __file__, "script_ver": "0.1", "description": "features from upload from %s" % (source_name)}]

            print feature_container_object_name,len(feature_container['features'])
            feature_container_string = simplejson.dumps(feature_container, sort_keys=True, indent=4)
            feature_container_file = open(feature_container_object_name+'.json', 'w+')
            feature_container_file.write(feature_container_string)
            feature_container_file.close()

#            logger.info("Attempting save of Feature Container %s" % (feature_container_object_name))
#            feature_container_not_saved = True
#            while feature_container_not_saved:
#                try:
#            feature_container_info =  ws_client.save_objects({"workspace":workspace_name,
#                                                              "objects":[ { "type":"KBaseGenomeAnnotations.FeatureContainer",
#                                                                            "data":feature_container,
#                                                                            "name": feature_container_object_name,
#                                                                            "provenance":feature_container_provenance}]}) 
#                    feature_container_not_saved = False 
#            logger.info("Feature Container saved for %s" % (feature_container_object_name)) 
#                except biokbase.workspace.client.ServerError as err: 
#                    #KEEPS GOING FOR NOW.  DO WE WANT TO HAVE A LIMIT?
#                    raise 

    protein_container_object_name = "%s_protein_container" % (core_genome_name)
    protein_reference = None
    if len(protein_container_dict) > 0: 
        protein_container = dict()
        protein_container['protein_container_id'] = protein_container_object_name 
        protein_container['name'] = protein_container_object_name
        protein_container['notes'] = "Proteins uploaded from %s" % (source_name)

        protein_reference = "%s/%s" % (workspace_name, protein_container_object_name)

        features_type_counts['protein'] = len(protein_container_dict)
        protein_container['proteins'] = protein_container_dict

        protein_container_string = simplejson.dumps(protein_container, sort_keys=True, indent=4)
        protein_container_file = open(protein_container_object_name+'.json', 'w+')
        protein_container_file.write(protein_container_string)
        protein_container_file.close()

        #Provencance has a 1 MB limit.  We may want to add more like the accessions, but to be safe for now not doing that.
        #provenance_description = "proteins from upload from %s includes accession(s) : " % (source_name,",".join(locus_name_order))
        protein_container_provenance = [{"script": __file__, "script_ver": "0.1", "description": "proteins from upload from %s" % (source_name)}]

#        while protein_container_not_saved:
#            try: 

#        print "PROTEIN CONTAINER : \n\n\n\n" + str(protein_container)

#        logger.info("Attempting Protein Container save for %s" % (protein_container_object_name))  
#        protein_container_info =  ws_client.save_objects({"workspace": workspace_name,
#                                                          "objects":[ { "type":"KBaseGenomeAnnotations.ProteinContainer",
#                                                                        "data":protein_container,
#                                                                        "name": protein_container_object_name,
#                                                                        "provenance":protein_container_provenance}]})
#        logger.info("Protein Container saved for %s" % (protein_container_object_name))  
#                protein_container_not_saved = False 
#            except biokbase.workspace.client.ServerError as err:
#                #KEEPS GOING FOR NOW.  DO WE WANT TO HAVE A LIMIT?
#                raise 
#    else:
#        raise Exception("No CDS annotations exist in this Genbank file.  This appears not to be a genome.  If this is just an assembly, you should upload it as an assembly using a fasta file.")

    genome_annotation = dict()
#genome_annotation['genbank_handle_ref'] = handle_id
    genome_annotation['feature_lookup'] = dict() #feature_lookup_dict
    genome_annotation['protein_container_ref'] = protein_reference
    genome_annotation['feature_container_references'] = features_container_references 
    genome_annotation['counts_map'] = counts_map
    genome_annotation['type'] = genome_type
    if genome_type == "Reference":
        genome_annotation['reference_annotation'] = 1
    else:
        genome_annotation['reference_annotation'] = 0

    genome_annotation_object_name = core_genome_name
    genome_annotation['genome_annotation_id'] = genome_annotation_object_name

    genome_annotation['taxon_ref'] = "" #taxon_id
    genome_annotation['assembly_ref'] = "" #assembly_reference

#genome_annotation['external_source'] = source_name
#genome_annotation['external_source_id'] = ",".join(locus_name_order)
#genome_annotation['external_source_origination_date'] = genbank_time_string
#genome_annotation['interfeature_relationship_counts_map'] = interfeature_relationship_counts_map
#genome_annotation['alias_source_counts_map'] = alias_source_counts_map
#genome_annotation['annotation_quality_ref'] = annotation_quality_reference

    genome_annotation_string = simplejson.dumps(genome_annotation, sort_keys=True, indent=4)
    genome_annotation_file = open(genome_annotation_object_name+'.json', 'w+')
    genome_annotation_file.write(genome_annotation_string)
    genome_annotation_file.close()

#genome_annotation_provenance = [{"script": __file__, "script_ver": "0.1", "description": "features from upload from %s" % (source_name)}]

#shock_id = None
#handle_id = None
#if shock_id is None:
#    shock_info = script_utils.upload_file_to_shock(logger, shock_service_url, input_file_name, token=token)
#    shock_id = shock_info["id"]
#    handles = script_utils.getHandles(logger, shock_service_url, handle_service_url, [shock_id], [handle_id], token)   
#    handle_id = handles[0]

