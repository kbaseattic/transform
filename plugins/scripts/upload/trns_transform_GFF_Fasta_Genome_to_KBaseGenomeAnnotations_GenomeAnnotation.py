#!/usr/bin/env python

#GFF3 format
#http://www.sequenceontology.org/gff3.shtml
#http://gmod.org/wiki/GFF3

# Standard imports
import sys,os,time,datetime,re
import itertools,hashlib,logging
import gzip,shutil

# 3rd party imports
import simplejson
from Bio.Seq import Seq
from Bio.Alphabet import IUPAC
from Bio.Data import CodonTable

# KBase imports
import biokbase.workspace.client 
import biokbase.Transform.script_utils as script_utils
import trns_transform_FASTA_DNA_Assembly_to_KBaseGenomeAnnotations_Assembly as assembly

def upload_genome(input_gff_file=None, input_fasta_file=None, workspace_name=None,
                  shock_service_url=None, handle_service_url=None, workspace_service_url=None,
                  taxon_reference = None, source=None, release=None, core_genome_name=None, genome_type=None,scientific_name=None,
                  level=logging.INFO, logger=None):

    ws_client = biokbase.workspace.client.Workspace(workspace_service_url)

    #No time string stored in GFF
    #Fasta file headers have time strings
    time_string = str(datetime.datetime.fromtimestamp(time.time()).strftime('%Y_%m_%d_%H_%M_%S'))

    logger.info("Uploading Assembly")
    assembly_name = "%s_assembly" % (core_genome_name)
    assembly_reference = "%s/%s" % (workspace_name,assembly_name)
    input_directory = "/".join(input_fasta_file.split("/")[0:-1])
    
    #Files should be gzipped
    with gzip.open(input_fasta_file, 'rb') as f_in:
        with open(input_fasta_file[0:-3], 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)

    try:
        assembly.upload_assembly(shock_service_url = shock_service_url,
                                 handle_service_url = handle_service_url,
                                 workspace_service_url = workspace_service_url,
                                 input_directory = input_directory,
                                 workspace_name = workspace_name,
                                 assembly_name = assembly_name,
                                 source = source,
                                 date_string = time_string,
                                 taxon_reference = taxon_reference,
                                 logger = logger)

#                                 contig_information_dict = contig_information_dict,

    except Exception, e: 
        logger.exception(e) 
        sys.exit(1) 

    logger.info("Assembly Uploaded as "+assembly_reference)
    os.remove(args.input_fasta_file[0:-3])

    ##########################################
    #Reading in Fasta file, Code taken from https://www.biostars.org/p/710/
    ##########################################
    logger.info("Reading FASTA file.") 

    contigs_sequences = dict()
    input_file_handle = gzip.open(input_fasta_file,'rb')
    # ditch the boolean (x[0]) and just keep the header or sequence since
    # we know they alternate.
    faiter = (x[1] for x in itertools.groupby(input_file_handle, lambda line: line[0] == ">"))
    for header in faiter:
        # drop the ">"
        header = header.next()[1:].strip()
        # join all sequence lines to one.
        seq = "".join(s.strip() for s in faiter.next())

        try:
            fasta_header,fasta_description = header.split(' ',1)
        except:
            fasta_header = header
            fasta_description = None

        contigs_sequences[fasta_header]= {'description':fasta_description,'sequence':seq}

    logger.info("Reading GFF file.") 

    header = list()
    feature_list = dict()

    gff_file_handle = gzip.open(input_gff_file, 'rb')
    current_line = gff_file_handle.readline()
    while ( current_line != '' ):
        current_line=current_line.strip()
        
        if(current_line.startswith("##")):
            header.append(current_line)
        else:
            contig_id, source, feature_type, start, end, score, strand, phase, attributes = current_line.split('\t')
            if(contig_id not in contigs_sequences):
                logger.warn("Missing contig: "+contig_id)

            if(contig_id not in feature_list):
                feature_list[contig_id]=list()

            feature = {'type':feature_type,'start':int(start),'end':int(end),'score':score,'strand':strand,'phase':phase}
            for attribute in attributes.split(";"):
                key, value = attribute.split("=")
                feature[key]=value
            
            feature_list[contig_id].append(feature)

        current_line = gff_file_handle.readline()

    features_type_containers_dict = dict()
    features_type_id_counter_dict = dict()
    features_container_references = dict()
    feature_grouping_dict = { "gene_with_mRNA" : {}, "mRNA_with_gene" : {}, "mRNA_with_CDS" : {},
                              "gene_with_CDS" : {}, "CDS_with_gene" : {}, "CDS_with_mRNA" : {}, "mRNA_with_UTR" : {} }

    feature_id_map_dict = dict()
    features_type_counts_map = dict()
 
    alias_source_counts_map = dict()

    aggregated_cds_map = dict()

    for contig in sorted(feature_list):
        for feature in feature_list[contig]:
            #To consider:
            #feature_object["function"] = value
            #feature_object["trans_splicing"] = 1
            #feature_object["additional_properties"] = additional_properties
            #feature_object["notes"] = notes
            #feature_object["inference"] = inference

            feature_object = dict()
            feature_object["type"]=feature["type"]
            if feature['type'] not in features_type_containers_dict:
                features_type_containers_dict[feature['type']] = dict()

            if feature['type'] not in features_type_id_counter_dict:
                features_type_id_counter_dict[feature['type']] = 1
                feature_id = "%s_%s" % (feature['type'],str(1)) 
            else: 
                features_type_id_counter_dict[feature['type']] += 1 
                feature_id = "%s_%s" % (feature['type'],str(features_type_id_counter_dict[feature['type']]))

            feature_object["feature_id"]=feature_id

            #GFF use 1-based integers
            substr_start = feature["start"]-1 
            substr_end = feature["end"]
            if(feature["strand"] == "-"):
                substr_start = feature["end"]-1
                substr_end = feature["start"]

            dna_sequence = Seq(contigs_sequences[contig]["sequence"][feature["start"]-1:feature["end"]], IUPAC.ambiguous_dna)
            
            if(feature["strand"] == "-"):
                #reverse complement
                dna_sequence = dna_sequence.reverse_complement()

            feature_object["dna_sequence"]=str(dna_sequence).upper()
            feature_object["dna_sequence_length"]=len(dna_sequence)
            feature_object["md5"]=hashlib.md5(str(dna_sequence)).hexdigest()
            feature_object["locations"]=[[contig,feature["start"],feature["strand"],len(dna_sequence)]]

            feature_object["quality_warnings"]=list()

            alias_dict = { feature["ID"] : [ "Original "+feature["type"]+" ID" ] }
            feature_id_map_dict[feature["ID"]] = feature_id
            feature_id_map_dict[feature_id] = feature["ID"]
            if("Name" in feature):
                alias_dict[feature["Name"]] = ["Original "+feature["type"]+" Name"]
            if("pacid" in feature):
                alias_dict[feature["pacid"]] = ["Original "+feature["type"]+" PAC ID"]
            feature_object["aliases"]=alias_dict
    
            for alias in alias_dict:
                for source in alias_dict[alias]:
                    if(source not in alias_source_counts_map):
                        alias_source_counts_map[source]=1
                    else:
                        alias_source_counts_map[source]+=1

            if("Parent" in feature and feature["type"] == "mRNA"):
                grouping_tuples = [("gene_with_mRNA",feature["Parent"],feature["ID"]),("mRNA_with_gene",feature["ID"],feature["Parent"])]

                for group in grouping_tuples:
                    if(group[1] not in feature_grouping_dict[group[0]]):
                        feature_grouping_dict[group[0]][group[1]] = {}
                    feature_grouping_dict[group[0]][group[1]][group[2]]=1

            if(feature["type"] == "gene"):
                feature_object["gene_properties"]={ "children_CDS" : [], "children_mRNA" : [] }
            if(feature["type"] == "mRNA"):
                feature_object["mRNA_properties"]={ "parent_gene" : ('gene',feature_id_map_dict[feature["Parent"]]), "associated_CDS" : ("CDS","") }
            if(feature["type"] == "CDS"):
                feature_object["CDS_properties"]= { "parent_gene" : ("gene",""), "associated_mRNA" : ("mRNA",feature_id_map_dict[feature["Parent"]]) }

                if(feature_id_map_dict[feature["Parent"]] not in aggregated_cds_map):
                    aggregated_cds_map[feature_id_map_dict[feature["Parent"]]]=list()
                aggregated_cds_map[feature_id_map_dict[feature["Parent"]]].append(feature_id)

            features_type_containers_dict[feature["type"]][feature_id] = feature_object
            
            if("UTR" in feature["type"]):
                if(feature_id_map_dict[feature["Parent"]] not in feature_grouping_dict["mRNA_with_UTR"]):
                    feature_grouping_dict["mRNA_with_UTR"][feature_id_map_dict[feature["Parent"]]]={}
                feature_grouping_dict["mRNA_with_UTR"][feature_id_map_dict[feature["Parent"]]][feature_id]=1

    #####################################################
    #Aggregate CDS
    #####################################################
    aggregated_cds=dict()
    for mRNA_id in aggregated_cds_map:
        for cds_id in sorted(aggregated_cds_map[mRNA_id], key = lambda x: int(x.split('_')[1])):
            CDS_Object = features_type_containers_dict["CDS"][cds_id]

            #Save first object, otherwise append sequence and location
            if(mRNA_id not in aggregated_cds):
                aggregated_cds[mRNA_id]=CDS_Object
            else:
                aggregated_cds[mRNA_id]["dna_sequence"]+=CDS_Object["dna_sequence"]
                aggregated_cds[mRNA_id]["locations"].append(CDS_Object["locations"][0])

    #############################
    #Refill features_type_containers_dict["CDS"]
    #and build up protein objects
    #############################

    protein_container_dict = dict()
    protein_id_counter = 1;

    features_type_containers_dict["CDS"]=dict()
    features_type_id_counter_dict["CDS"]=0

    for mRNA in sorted(aggregated_cds, key=lambda x: int(x.split('_')[1])):
        features_type_id_counter_dict["CDS"] += 1
        feature_id = "CDS_%s" % (str(features_type_id_counter_dict["CDS"]))

        if("dna_sequence" in aggregated_cds[mRNA]):
            #Build up the protein object for the protein container
            protein_object = dict()
            protein_id = "protein_%s" % (str(protein_id_counter))
            protein_id_counter += 1
            protein_object["protein_id"] = protein_id
            
            #Translate protein sequence
            dna_sequence = Seq(aggregated_cds[mRNA]["dna_sequence"], IUPAC.ambiguous_dna)
            rna_sequence = dna_sequence.transcribe()
            protein_sequence = Seq("")
            try: 
                protein_sequence = rna_sequence.translate(cds=True)
            except CodonTable.TranslationError as te:
                print "TranslationError for "+feature_id_map_dict[mRNA]+": "+str(te)

            protein_object["amino_acid_sequence"] = str(protein_sequence).upper()
            protein_object["md5"] = hashlib.md5(protein_object["amino_acid_sequence"]).hexdigest()

            if "function" in aggregated_cds[mRNA]:
                protein_object["function"] = aggregated_cds[mRNA]["function"]

            protein_object["aliases"]=dict()
            if "aliases" in aggregated_cds[mRNA]:
                protein_object["aliases"] = aggregated_cds[mRNA]["aliases"]

            protein_container_dict[protein_object["protein_id"]] = protein_object
            protein_container_object_name = "%s_protein_container" % (core_genome_name)
            protein_ref = "%s/%s" % (workspace_name,protein_container_object_name)

        features_type_containers_dict["CDS"][feature_id]=aggregated_cds[mRNA]
        feature_id_map_dict[mRNA+".CDS"]=feature_id

        grouping_tuples = [("mRNA_with_CDS",feature_id_map_dict[mRNA],mRNA+".CDS"),("CDS_with_mRNA",mRNA+".CDS",feature_id_map_dict[mRNA])]
        feature_grouping_dict["mRNA_with_CDS"][feature_id_map_dict[mRNA]]={}

        for group in grouping_tuples:
            if(group[1] not in feature_grouping_dict[group[0]]):
                feature_grouping_dict[group[0]][group[1]] = {}
            feature_grouping_dict[group[0]][group[1]][group[2]]=1

    #####################################################
    #Update mRNA locations
    #Should be aggregate of UTRs and CDSs
    #####################################################
    for mRNA_id in features_type_containers_dict["mRNA"].keys():
        features_type_containers_dict["mRNA"][mRNA_id]["dna_sequence"]=""
        features_type_containers_dict["mRNA"][mRNA_id]["locations"]=[]

        #Build with five_prime, then CDS, then three_prime
        #Respectively, they may be missing, which is OK, but it's reported nonetheless
        if(mRNA_id in feature_grouping_dict["mRNA_with_UTR"]):
            UTR_Type = "five_prime_UTR"
            for UTR_id in feature_grouping_dict["mRNA_with_UTR"][mRNA_id]:
                if(UTR_Type in UTR_id):
                    features_type_containers_dict["mRNA"][mRNA_id]["locations"].append(features_type_containers_dict[UTR_Type][UTR_id]["locations"][0])
                    features_type_containers_dict["mRNA"][mRNA_id]["dna_sequence"]+=features_type_containers_dict[UTR_Type][UTR_id]["dna_sequence"]
        else:
            print "Missing UTR :",mRNA_id,feature_id_map_dict[mRNA_id]

        if(feature_id_map_dict[mRNA_id] in feature_grouping_dict["mRNA_with_CDS"]):
            for CDS_id in sorted(feature_grouping_dict["mRNA_with_CDS"][feature_id_map_dict[mRNA_id]], key = lambda x: int(re.split('[_.]',x)[1])):
                print "Adding CDS :",mRNA_id,features_type_containers_dict["mRNA"][mRNA_id]["locations"]
                print "Adding CDS :",CDS_id,features_type_containers_dict["CDS"][feature_id_map_dict[CDS_id]]["locations"][0]
                features_type_containers_dict["mRNA"][mRNA_id]["locations"].append(features_type_containers_dict["CDS"][feature_id_map_dict[CDS_id]]["locations"][0])
                features_type_containers_dict["mRNA"][mRNA_id]["dna_sequence"]+=features_type_containers_dict["CDS"][feature_id_map_dict[CDS_id]]["dna_sequence"]
        else:
            print "Missing CDS :",mRNA_id,feature_id_map_dict[mRNA_id]

        if(mRNA_id in feature_grouping_dict["mRNA_with_UTR"]):
            UTR_Type = "three_prime_UTR"
            for UTR_id in feature_grouping_dict["mRNA_with_UTR"][mRNA_id]:
                if(UTR_Type in UTR_id):
                    features_type_containers_dict["mRNA"][mRNA_id]["locations"].append(features_type_containers_dict[UTR_Type][UTR_id]["locations"][0])
                    features_type_containers_dict["mRNA"][mRNA_id]["dna_sequence"]+=features_type_containers_dict[UTR_Type][UTR_id]["dna_sequence"]

    #####################################################
    #Process relationships (to and from gene, mRNA, and CDS)
    #####################################################
    interfeature_relationship_counts_map = { "gene_with_mRNA" : len(feature_grouping_dict["gene_with_mRNA"]), "mRNA_with_CDS" : len(feature_grouping_dict["mRNA_with_CDS"]),
                                             "mRNA_with_gene" : len(feature_grouping_dict["mRNA_with_gene"]), "CDS_with_mRNA" : len(feature_grouping_dict["CDS_with_mRNA"]),
                                             "gene_with_CDS" : 0, "CDS_with_gene" : 0 }

    for gene in feature_grouping_dict["gene_with_mRNA"]:
        gene_id = feature_id_map_dict[gene]
        for mRNA in feature_grouping_dict["gene_with_mRNA"][gene]:
            mRNA_id = feature_id_map_dict[mRNA]
            features_type_containers_dict["gene"][gene_id]["gene_properties"]["children_mRNA"].append( ["mRNA",mRNA_id] )
            features_type_containers_dict["mRNA"][mRNA_id]["mRNA_properties"]["parent_gene"] = ["gene",gene_id]
    
    for mRNA in feature_grouping_dict["mRNA_with_CDS"]:
        mRNA_id = feature_id_map_dict[mRNA]
        for CDS in feature_grouping_dict["mRNA_with_CDS"][mRNA]:
            CDS_id = feature_id_map_dict[CDS]
            features_type_containers_dict["CDS"][CDS_id]["CDS_properties"]["associated_mRNA"] = ["mRNA",mRNA_id]
            features_type_containers_dict["mRNA"][mRNA_id]["mRNA_properties"]["associated_CDS"] = ["CDS",CDS_id]

            for gene in feature_grouping_dict["mRNA_with_gene"][mRNA]:
                gene_id = feature_id_map_dict[gene]
    
                if(CDS not in feature_grouping_dict["CDS_with_gene"]):
                    feature_grouping_dict["CDS_with_gene"][CDS]={}
                feature_grouping_dict["CDS_with_gene"][CDS][gene]=1

                if(gene not in feature_grouping_dict["gene_with_CDS"]):
                    feature_grouping_dict["gene_with_CDS"][gene]={}
                feature_grouping_dict["gene_with_CDS"][gene][CDS]=1

                features_type_containers_dict["CDS"][CDS_id]["CDS_properties"]["parent_gene"] = ["gene",gene_id]
                features_type_containers_dict["gene"][gene_id]["gene_properties"]["children_CDS"].append( ["CDS",CDS_id] )

    interfeature_relationship_counts_map["gene_with_CDS"] = len(feature_grouping_dict["gene_with_CDS"])
    interfeature_relationship_counts_map["CDS_with_gene"] = len(feature_grouping_dict["CDS_with_gene"])

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

            features_type_counts_map[feature_type] = len(features_type_containers_dict[feature_type])

            #Provenance has a 1 MB limit.  We may want to add more like the accessions, but to be safe for now not doing that.
            #provenance_description = "features from upload from %s includes accession(s) : " % (source,",".join(locus_name_order))
            feature_container_provenance = [{"script": __file__, "script_ver": "0.1", "description": "features from upload from %s" % (source)}]

            print feature_container_object_name,len(feature_container['features'])
            feature_container_string = simplejson.dumps(feature_container, sort_keys=True, indent=4)
            feature_container_file = open(feature_container_object_name+'.json', 'w+')
            feature_container_file.write(feature_container_string)
            feature_container_file.close()

            logger.info("Attempting save of Feature Container %s" % (feature_container_object_name))
            feature_container_not_saved = True
            while feature_container_not_saved:
                try:
                    feature_container_info =  ws_client.save_objects({"workspace":workspace_name,
                                                                      "objects":[ { "type": "KBaseGenomeAnnotations.FeatureContainer",
                                                                                    "data": feature_container,
                                                                                    "name": feature_container_object_name,
                                                                                    "hidden" : 1,
                                                                                    "provenance": feature_container_provenance}]}) 
                    feature_container_not_saved = False 
                    logger.info("Feature Container saved for %s" % (feature_container_object_name)) 
                except biokbase.workspace.client.ServerError as err: 
                    raise

    protein_container_object_name = "%s_protein_container" % (core_genome_name)
    protein_reference = None
    if len(protein_container_dict) > 0: 
        protein_container = dict()
        protein_container['protein_container_id'] = protein_container_object_name 
        protein_container['name'] = protein_container_object_name
        protein_container['notes'] = "Proteins uploaded from %s" % (source)

        protein_reference = "%s/%s" % (workspace_name, protein_container_object_name)

        features_type_counts_map['protein'] = len(protein_container_dict)
        protein_container['proteins'] = protein_container_dict

        protein_container_string = simplejson.dumps(protein_container, sort_keys=True, indent=4)
        protein_container_file = open(protein_container_object_name+'.json', 'w+')
        protein_container_file.write(protein_container_string)
        protein_container_file.close()

        #Provencance has a 1 MB limit.  We may want to add more like the accessions, but to be safe for now not doing that.
        #provenance_description = "proteins from upload from %s includes accession(s) : " % (source,",".join(locus_name_order))
        protein_container_provenance = [{"script": __file__, "script_ver": "0.1", "description": "proteins from upload from %s" % (source)}]
        protein_container_not_saved=True
        while protein_container_not_saved:
            try: 
                logger.info("Attempting Protein Container save for %s" % (protein_container_object_name))  
                protein_container_info =  ws_client.save_objects({"workspace": workspace_name,
                                                                  "objects":[ { "type": "KBaseGenomeAnnotations.ProteinContainer",
                                                                                "data": protein_container,
                                                                                "name": protein_container_object_name,
                                                                                "hidden": 1,
                                                                                "provenance": protein_container_provenance}]})
                logger.info("Protein Container saved for %s" % (protein_container_object_name))  
                protein_container_not_saved = False 
            except biokbase.workspace.client.ServerError as err:
                raise 

    genome_annotation = dict()

    #Upload GFF to shock
    token = os.environ.get('KB_AUTH_TOKEN') 
    shock_id = None
    handle_id = None
    if shock_id is None:
        shock_info = script_utils.upload_file_to_shock(logger, shock_service_url, input_gff_file, token=token)
        shock_id = shock_info["id"]
        handles = script_utils.getHandles(logger, shock_service_url, handle_service_url, [shock_id], [handle_id], token)   
        handle_id = handles[0]
    genome_annotation['gff_handle_ref'] = handle_id

    genome_annotation['feature_lookup'] = dict() #feature_lookup_dict
    genome_annotation['protein_container_ref'] = protein_reference
    genome_annotation['feature_container_references'] = features_container_references 
    genome_annotation['counts_map'] = features_type_counts_map
    genome_annotation['type'] = genome_type

    if genome_type == "Reference":
        genome_annotation['reference_annotation'] = 1
    else:
        genome_annotation['reference_annotation'] = 0

    genome_annotation_object_name = core_genome_name
    genome_annotation['genome_annotation_id'] = genome_annotation_object_name

    genome_annotation['display_sc_name']=scientific_name
    genome_annotation['taxon_ref'] = taxon_reference
    genome_annotation['assembly_ref'] = assembly_reference
    genome_annotation['original_source_file_name']=input_gff_file

    genome_annotation['interfeature_relationship_counts_map'] = interfeature_relationship_counts_map
    print interfeature_relationship_counts_map

    genome_annotation['alias_source_counts_map'] = alias_source_counts_map
    genome_annotation['external_source'] = source
    genome_annotation['external_source_origination_date'] = time_string
    genome_annotation['release'] = release

#genome_annotation['external_source_id'] = ",".join(locus_name_order)
#genome_annotation['annotation_quality_ref'] = annotation_quality_reference

    genome_annotation_string = simplejson.dumps(genome_annotation, sort_keys=True, indent=4)
    genome_annotation_file = open(genome_annotation_object_name+'.json', 'w+')
    genome_annotation_file.write(genome_annotation_string)
    genome_annotation_file.close()

    #Provencance has a 1 MB limit.  We may want to add more like the accessions, but to be safe for now not doing that.
    genome_annotation_provenance = [{"script": __file__, "script_ver": "0.1", "description": "GenomeAnnotation from upload from %s" % (source)}]

    logger.info("Attempting Genome Annotation save for %s" % (genome_annotation_object_name))
    genome_annotation_not_saved = True
    while genome_annotation_not_saved:
        try:
            genome_annotation_info =  ws_client.save_objects({"workspace":workspace_name,
                                                              "objects":[ { "type": "KBaseGenomeAnnotations.GenomeAnnotation",
                                                                            "data": genome_annotation,
                                                                            "name": genome_annotation_object_name,
                                                                            "provenance": genome_annotation_provenance}]}) 
            genome_annotation_not_saved = False 
            logger.info("Genome Annotation saved for %s" % (genome_annotation_object_name))
        except biokbase.workspace.client.ServerError as err: 
            raise

if __name__ == "__main__":

    import argparse

    parser = argparse.ArgumentParser(prog=__file__)

    parser.add_argument('--input_gff_file', nargs='?', help='GFF file', required=True)
    parser.add_argument('--input_fasta_file', nargs='?', help='FASTA file', required=True)
    parser.add_argument('--workspace_name', nargs='?', help='Workspace to populate', required=True)

    parser.add_argument('--shock_service_url', type=str, nargs='?', required=False, default='https://ci.kbase.us/services/shock-api/')
    parser.add_argument('--handle_service_url', type=str, nargs='?', required=False, default='https://ci.kbase.us/services/handle_service/')
    parser.add_argument('--workspace_service_url', type=str, nargs='?', required=False, default='https://ci.kbase.us/services/ws/')

    parser.add_argument('--organism', nargs='?', help='Taxon', required=True)
    parser.add_argument('--taxon_wsname', nargs='?', help='Taxon Workspace', required=False, default='ReferenceTaxons')
    parser.add_argument('--taxon_names_file', nargs='?', help='Taxon Mappings', required=False)

    parser.add_argument('--source', help="data source : examples Refseq, Genbank, Pythozyme, Gramene, etc", nargs='?', required=False, default="Phytozome") 
    parser.add_argument('--release', help="Release or version of the data.  Example Ensembl release 30", nargs='?', required=False, default = "11") 

    args, unknown = parser.parse_known_args()

    logger = script_utils.stderrlogger(__file__)
    logger.debug(args)

    if not os.path.isfile(args.input_gff_file):
        logger.warning("{0} is not a recognizable file".format(args.input_gff_file))

    if(args.input_gff_file[-3:len(args.input_gff_file)] != '.gz'):
        logger.warning("{0} is not a gzipped file".format(args.input_gff_file))

    if not os.path.isfile(args.input_fasta_file):
        logger.warning("{0} is not a recognizable file".format(args.input_fasta_file))

    if(args.input_fasta_file[-3:len(args.input_fasta_file)] != '.gz'):
        logger.warning("{0} is not a gzipped file".format(args.input_fasta_file))

    ws_client = biokbase.workspace.client.Workspace(args.workspace_service_url)

    #Get the taxon_lookup_object
    taxon_lookup = ws_client.get_object( {'workspace':args.taxon_wsname,
                                          'id':"taxon_lookup"})['data']['taxon_lookup']
    
    #Taxon lookup dependent on full genus
    #Can use a file that has two columns, and will translate the organism text into what's in the second column
    #In order to match what's in the taxon lookup
    #Example: Athaliana    Arabidopsis thaliana
    if(args.taxon_names_file is not None):
        if(os.path.isfile(args.taxon_names_file)):
            for line in open(args.taxon_names_file):
                line=line.strip()
                array=line.split('\t')
                if(args.organism in array[0]):
                    args.organism = array[1]
                    break
        else:
            print "Warning taxon_names_file argument (%s) doesn't exist" % args.taxon_names_file

    tax_id=0
    taxon_object_name = "unknown_taxon"
    display_sc_name = None

    if(args.organism[0:3] in taxon_lookup and args.organism in taxon_lookup[args.organism[0:3]]):
        tax_id=taxon_lookup[args.organism[0:3]][args.organism]
        taxon_object_name = "%s_taxon" % (str(tax_id))

    taxon_info = ws_client.get_objects([{"workspace": args.taxon_wsname, 
                                         "name": taxon_object_name}])[0]

    taxon_ref = "%s/%s/%s" % (taxon_info['info'][6], taxon_info['info'][0], taxon_info['info'][4])
    display_sc_name = taxon_info['data']['scientific_name']

    core_genome_name = "%s_%s" % (tax_id,args.source) 
    genome_type="Reference"
    upload_genome(input_gff_file=args.input_gff_file,input_fasta_file=args.input_fasta_file,workspace_name=args.workspace_name,
                  shock_service_url=args.shock_service_url,handle_service_url=args.handle_service_url,workspace_service_url=args.workspace_service_url,
                  taxon_reference=taxon_ref,source=args.source,release=args.release,core_genome_name=core_genome_name,genome_type=genome_type,scientific_name=display_sc_name,
                  logger=logger)
    sys.exit(0)
