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
import urllib
import gzip
import datetime
import trns_transform_Genbank_Genome_to_KBaseGenomeAnnotations_GenomeAnnotation as genome_annotation



def upload_ensembl_plants(release_source = None,
                          release = None,
                          workspace_name = None,
                          ensembl_ftp_urls_file = None,
                          shock_service_url = None,
                          handle_service_url = None,
                          taxon_wsname = None,
                          workspace_service_url = None):
    if taxon_wsname is None:
        taxon_wsname = 'ReferenceTaxons'
    if os.path.isfile(ensembl_ftp_urls_file): 
        print "Found ensembl_ftp_urls_file" 
        links_f = open(ensembl_ftp_urls_file, 'r') 
        counter = 1
        for line in links_f:
            if counter < 40:
                temp_list = re.split(r'\t', line)
                dir_name = temp_list[0]
                start_time = datetime.datetime.now()
                print "\nSTARTED PROCESSING : %s - %s" % (dir_name,str(start_time))
                file_source = temp_list[1].rstrip()
                dir_full_name = "data/%s" % (dir_name)
                ftp_path_elements = re.split(r'/', file_source)

                file_full_name = "data/%s/%s" % (dir_name,ftp_path_elements[-1])

                core_name = ftp_path_elements[-1].replace(".gz","")
                uncompressed_file_name = "data/%s/%s" % (dir_name,core_name)
                uncompress_end_time = None
                if not os.path.isdir(dir_full_name):
                    os.makedirs(dir_full_name)
                if not os.path.exists(uncompressed_file_name):
                    uncompressed_file = open(uncompressed_file_name,"w+")
            
                    fetch_start_time = datetime.datetime.now()
                    urllib.urlretrieve(file_source, file_full_name)
                    fetch_end_time = datetime.datetime.now()
                    fetch_total_time = fetch_end_time - fetch_start_time
                    print "Fetch total time : %s" % (str(fetch_total_time))

                    zip_file = gzip.open(file_full_name,"rb")
                    decoded = zip_file.read()
                    uncompressed_file.write(decoded)
                    zip_file.close()
                    os.remove(file_full_name)
                    uncompressed_file.close()
                    uncompress_end_time = datetime.datetime.now()
                    uncompress_total_time = uncompress_end_time - fetch_end_time
                    print "Uncompress total time : %s" % (str(uncompress_total_time))
                
                #DO Upload
                if uncompress_end_time is None:
                    uncompress_end_time = start_time

                try:
                    genome_annotation.upload_genome(shock_service_url=shock_service_url,
                                                    handle_service_url=handle_service_url,
                                                    input_directory=dir_full_name,
                                                    workspace_name=workspace_name,
                                                    workspace_service_url=workspace_service_url,
                                                    taxon_wsname=taxon_wsname,
                                                    exclude_feature_types=["misc_feature","STS"],
                                                    source=release_source, 
                                                    release=release,
                                                    type="Reference")
                    upload_end_time = datetime.datetime.now()
                    upload_total_time = upload_end_time - uncompress_end_time 
                    print "Upload total time : %s" % (str(upload_total_time)) 
                except Exception, e:
                    print "FAILED UPLOAD %s" % (dir_full_name)
                    raise Exception(e)

            counter +=1
        print "Done"    
    else:
        raise Exception("No ensembl_ftp_urls_file found")
    



if __name__ == "__main__":
    import argparse 
 
    parser = argparse.ArgumentParser(prog=__file__, 
                                     description="UploadsEnsemblPlantsData", 
                                     epilog="Jason Baumohl") 
 
    parser.add_argument('--release_source',action='store', type=str, nargs='?', required=True) 
    parser.add_argument('--release',action='store', type=str, nargs='?', required=True) 
    parser.add_argument('--workspace_name',action='store', type=str, nargs='?', required=True) 
    parser.add_argument('--ensembl_ftp_urls_file',action='store', type=str, nargs='?', required=True) 
    parser.add_argument('--shock_service_url', action='store', type=str, nargs='?', required=True)
    parser.add_argument('--handle_service_url', action='store', type=str, nargs='?', default=None, required=True)
    parser.add_argument('--taxon_wsname', nargs='?', help='workspace name with taxon in it, assumes the same workspace_service_url', required=False, default='ReferenceTaxons') 
    parser.add_argument('--workspace_service_url', action='store', type=str, nargs='?', required=True) 

    args, unknown = parser.parse_known_args() 

    try:
        upload_ensembl_plants(release_source = args.release_source,
                              release = args.release,
                              workspace_name = args.workspace_name, 
                              ensembl_ftp_urls_file = args.ensembl_ftp_urls_file,
                              shock_service_url = args.shock_service_url,
                              handle_service_url = args.handle_service_url,
                              taxon_wsname = args.taxon_wsname,
                              workspace_service_url = args.workspace_service_url
        )
    except Exception, e: 
        raise Exception(e) 
        sys.exit(1) 
 
    sys.exit(0) 
