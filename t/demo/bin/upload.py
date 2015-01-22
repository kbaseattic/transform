#!/usr/bin/env python

import sys
import time
import datetime
import os
import os.path
import io
import bz2
import gzip
import zipfile
import tarfile
import pprint
import subprocess

# patch for handling unverified certificates
import ssl
if hasattr(ssl, '_create_unverified_context'):
    ssl._create_default_https_context = ssl._create_unverified_context

# make sure the 3rd party and kbase modules are in the path for importing
sys.path.insert(0,os.path.abspath("venv/lib/python2.7/site-packages/"))

from requests_toolbelt import MultipartEncoder, MultipartEncoderMonitor
import requests
import magic
import blessings
import dateutil.parser
import dateutil.tz
import simplejson

import biokbase.Transform.Client
import biokbase.Transform.script_utils
import biokbase.Transform.handler_utils
import biokbase.userandjobstate.client
import biokbase.workspace.client

logger = biokbase.Transform.script_utils.stdoutlogger(__file__)

configs = dict()

def read_configs(configs_directory):
    for x in os.listdir(configs_directory):
        with open(os.path.join(configs_directory,x), 'r') as f:
            c = simplejson.loads(f.read())
            configs[c["script_type"]] = c
    

def validate_files(input_directory, external_type):
    if external_type in configs["validate"]:
        print "validate"


def show_workspace_object_list(workspace_url, workspace_name, object_name, token):
    print term.blue("\tYour KBase data objects:")
    
    c = biokbase.workspace.client.Workspace(workspace_url, token=token)
    object_list = c.list_objects({"workspaces": [workspace_name]})
    
    object_list = [x for x in object_list if object_name in x[1]]

    for x in sorted(object_list):
        elapsed_time = datetime.datetime.utcnow().replace(tzinfo=dateutil.tz.tzutc()) - dateutil.parser.parse(x[3])
        print "\t\thow_recent: {0}\n\t\tname: {1}\n\t\ttype: {2}\n\t\tsize: {3:d}\n".format(elapsed_time, x[1], x[2], x[-2])


def show_workspace_object_contents(workspace_url, workspace_name, object_name, token):
    c = biokbase.workspace.client.Workspace(workspace_url, token=token)
    object_contents = c.get_objects([{"workspace": workspace_name, "objid": 2}])
    print object_contents


def show_job_progress(ujs_url, awe_url, awe_id, ujs_id, token):
    c = biokbase.userandjobstate.client.UserAndJobState(url=ujs_url, token=token)

    completed = ["complete", "success"]
    error = ["error", "fail", "ERROR"]
    
    term = blessings.Terminal()

    header = dict()
    header["Authorization"] = "Oauth %s" % token

    print term.blue("\tUJS Job Status:")
    # wait for UJS to complete    
    last_status = ""
    time_limit = 40
    start = datetime.datetime.utcnow()
    while 1:        
        try:
            status = c.get_job_status(ujs_id)
        except Exception, e:
            print term.red("\t\tIssue connecting to UJS!")
            status[1] = "ERROR"
            status[2] = "Caught Exception"
        
        if (datetime.datetime.utcnow() - start).seconds > time_limit:
            print "\t\tJob is taking longer than it should, check debugging messages for more information."
            status[1] = "ERROR"
            status[2] = "Timeout"            
        
        if last_status != status[2]:
            print "\t\t{0} status update: {1}".format(status[0], status[2])
            last_status = status[2]
        
        if status[1] in completed or status[1] in error:
            print term.green("\t\tKBase upload completed!\n")
            break
        elif status[1] in error:
            print term.red("\t\tOur job failed!\n")
            
            print term.red("{0}".format(c.get_detailed_error(ujs_id)))
            print term.red("{0}".format(c.get_results(ujs_id)))
            
            print term.bold("Additional AWE job details for debugging")
            # check awe job output
            awe_details = requests.get("{0}/job/{1}".format(awe_url,awe_id), headers=header, verify=True)
            job_info = awe_details.json()["data"]
            print term.red(simplejson.dumps(job_info, sort_keys=True, indent=4))
            
            awe_stdout = requests.get("{0}/work/{1}?report=stdout".format(awe_url,job_info["tasks"][0]["taskid"]+"_0"), headers=header, verify=True)
            print term.red("STDOUT : " + simplejson.dumps(awe_stdout.json()["data"], sort_keys=True, indent=4))
            
            awe_stderr = requests.get("{0}/work/{1}?report=stderr".format(awe_url,job_info["tasks"][0]["taskid"]+"_0"), headers=header, verify=True)
            print term.red("STDERR : " + simplejson.dumps(awe_stderr.json()["data"], sort_keys=True, indent=4))
            
            break
    

def upload(transform_url, options, token):
    c = biokbase.Transform.Client.Transform(url=transform_url, token=token)
    response = c.upload(options)        
    return response



def post_to_shock(shockURL, filePath, token):
    size = os.path.getsize(filePath)

    term = blessings.Terminal()
    
    print term.blue("\tShock upload status:\n")
    def progress_indicator(monitor):
        if monitor.bytes_read > size:
            pass            
        else:
            progress = int(monitor.bytes_read)/float(size) * 100.0
            print term.move_up + term.move_left + "\t\tPercentage of bytes uploaded to shock {0:.2f}%".format(progress)                    
            
    #build the header
    header = dict()
    header["Authorization"] = "Oauth %s" % token

    dataFile = open(os.path.abspath(filePath))
    encoder = MultipartEncoder(fields={'upload': (os.path.split(filePath)[-1], dataFile)})
    header['Content-Type'] = encoder.content_type
    
    m = MultipartEncoderMonitor(encoder, progress_indicator)

    response = requests.post(shockURL + "/node", headers=header, data=m, allow_redirects=True, verify=True)
    
    if not response.ok:
        print response.raise_for_status()

    result = response.json()

    if result['error']:
        raise Exception(result['error'][0])
    else:
        return result["data"]    


def download_from_shock(shockURL, shock_id, filePath, token):
    header = dict()
    header["Authorization"] = "Oauth %s" % token
    
    data = requests.get(shockURL + '/node/' + shock_id + "?download_raw", headers=header, stream=True)
    size = int(data.headers['content-length'])
    
    chunkSize = 10 * 2**20
    download_iter = data.iter_content(chunkSize)

    term = blessings.Terminal()
    f = open(filePath, 'wb')

    downloaded = 0
    try:
        for chunk in download_iter:
            f.write(chunk)
            
            if downloaded + chunkSize > size:
                downloaded = size
            else:
                downloaded += chunkSize
        
            print term.move_up + term.move_left + "\tDownloaded from shock {0:.2f}%".format(downloaded/float(size) * 100.0)
    except:
        raise        
    finally:
        f.close()
        data.close()
        
    print "\tFile size : {0:f} MB".format(int(os.path.getsize(filePath))/float(1024*1024))

    biokbase.Transform.script_utils.extract_data(logger, filePath)



if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='KBase Upload demo and client')
    parser.add_argument('--demo', action="store_true")
    parser.add_argument('--shock_service_url', nargs='?', help='SHOCK service to upload local files', const="", default="https://kbase.us/services/shock-api/")
    parser.add_argument('--ujs_service_url', nargs='?', help='UserandJobState service for monitoring progress', const="", default="https://kbase.us/services/userandjobstate/")
    parser.add_argument('--workspace_service_url', nargs='?', help='Workspace service for KBase objects', const="", default="https://kbase.us/services/ws/")
    parser.add_argument('--awe_service_url', nargs='?', help='AWE service for additional job monitoring', const="", default="http://140.221.67.242:7080")
    parser.add_argument('--transform_service_url', nargs='?', help='Transform service that handles the data conversion to KBase', const="", default="http://140.221.67.242:7778/")
    parser.add_argument('--handle_service_url', nargs='?', help='Handle service for KBase handle', const="", default="https://kbase.us/services/handle_service")

    parser.add_argument('--external_type', nargs='?', help='the external type of the data', const="", default="")
    parser.add_argument('--kbase_type', nargs='?', help='the kbase object type to create', const="", default="")
    parser.add_argument('--workspace', nargs='?', help='name of the workspace where your objects should be created', const="", default="upload_testing")
    parser.add_argument('--object_name', nargs='?', help='name of the workspace object to create', const="", default="")
    parser.add_argument('--file_path', nargs='?', help='path to file for upload', const="", default="")
    parser.add_argument('--url_mapping', nargs='?', help='dictionary of urls to process', const="", default="")
    parser.add_argument('--download_path', nargs='?', help='path to place downloaded files for validation', const=".", default=".")
    parser.add_argument('--handler', help='Client bypass test', dest="handler_mode", action='store_true')
    parser.add_argument('--client', help='Client mode test', dest="handler_mode", action='store_false')
    parser.set_defaults(handler_mode=False)
    ## TODO: change the default path to be relative to __FILE__
    parser.add_argument('--plugin_directory', nargs='?', help='path to the plugin dir', const="", default="/kb/dev_container/modules/transform/plugins/configs")

    args = parser.parse_args()

    token = os.environ.get("KB_AUTH_TOKEN")
    if token is None:
        if os.path.exists(os.path.expanduser("~/.kbase_config")):
            f = open(os.path.expanduser("~/.kbase_config"), 'r')
            config = f.read()
            if "token=" in config:
                token = config.split("token=")[1].split("\n",1)[0]            
            else:
                raise Exception("Unable to find KBase token!")
        else:
            raise Exception("Unable to find KBase token!")

    #read_configs(os.path.abspath("../../plugins/configs"))
    

    plugin = None
    if args.handler_mode: 
        plugin = biokbase.Transform.handler_utils.PlugIns(args.plugin_directory, logger)

    inputs = list()
    if not args.demo:
        user_inputs = {"external_type": args.external_type,
                       "kbase_type": args.kbase_type,
                       "object_name": args.object_name,
                       "filePath": args.file_path,
                       "downloadPath": args.download_path,
                       "url_mapping" : args.url_mapping}

        workspace = args.workspace    
        inputs = [user_inputs]
    else:
        if "kbasetest" not in token and len(args.workspace.strip()) == 0:
            print "If you are running the demo as a different user than kbasetest, you need to provide the name of your workspace with --workspace."
            sys.exit(0)
        else:
            if args.workspace is not None:
                workspace = args.workspace

        fasta_to_contigset = {"external_type": "FASTA.DNA.Assembly",
                              "kbase_type": "KBaseGenomes.ContigSet",
                              "object_name": "fasciculatum_supercontig",
                              "filePath": "data/fasciculatum_supercontig.fasta.zip",
                              "downloadPath": "fasciculatum_supercontig.fasta.zip",
                              "url_mapping": "fasta_assembly"}

        genbank_to_contigset = {"external_type": "Genbank.ContigSet",
                         "kbase_type": "KBaseGenomes.ContigSet",
                         "object_name": "NC_005213",
                         "filePath": "data/genbank/NC_005213/NC_005213.gbk",
                         "downloadPath": "NC_005213.gbk"}

        genbank_to_genome = {"external_type": "Genbank.Genome",
                         "kbase_type": "KBaseGenomes.Genome",
                         "object_name": "NC_005213",
                         "filePath": "data/genbank/NC_005213/NC_005213.gbk",
                         "downloadPath": "NC_005213.gbk"}

        genbank_to_genome_ftp_ncbi_gz = {"external_type": "Genbank.Genome",
                            "kbase_type": "KBaseGenomes.Genome",
                            "object_name": "ecoli_reference.NCBI",
                            "filePath": None,
                            "downloadPath": None,
                            "url": "ftp://ftp.ncbi.nih.gov/genomes/genbank/bacteria/Escherichia_coli/reference/GCA_000005845.2_ASM584v2/GCA_000005845.2_ASM584v2_genomic.gbff.gz",
                            "url_mapping": "genbank_genome"}

        genbank_to_genome_http_mol_zip = {"external_type": "Genbank.Genome",
                            "kbase_type": "KBaseGenomes.Genome",
                            "object_name": "Abelson_murine_leukemia_virus.MOL",
                            "filePath": None,
                            "downloadPath": None,
                            "url": "http://www.microbesonline.org/cgi-bin/genomeInfo.cgi?tId=11788;export=gbk;compress=zip"}

        genbank_to_genome_ftp_patric = {"external_type": "Genbank.Genome",
                            "kbase_type": "KBaseGenomes.Genome",
                            "object_name": "Acetobacter_tropicalis_NBRC_101654.PATRIC",
                            "filePath": None,
                            "downloadPath": None,
                            "url": "ftp://ftp.patricbrc.org/patric2/genomes/Acetobacter_tropicalis_NBRC_101654/Acetobacter_tropicalis_NBRC_101654.PATRIC.gbf"}

        genbank_to_genome_ftp_refseq = {"external_type": "Genbank.Genome",
                            "kbase_type": "KBaseGenomes.Genome",
                            "object_name": "Acetobacter_tropicalis_NBRC_101654.Refseq",
                            "filePath": None,
                            "downloadPath": None,
                            "url": "ftp://ftp.patricbrc.org/patric2/genomes/Acetobacter_tropicalis_NBRC_101654/Acetobacter_tropicalis_NBRC_101654.RefSeq.gbf"}

        genbank_to_genome_ftp_ensembl = {"external_type": "Genbank.Genome",
                            "kbase_type": "KBaseGenomes.Genome",
                            "object_name": "Tursiops_truncatus.turTru1.78.nonchromosomal.ENSEMBL",
                            "filePath": None,
                            "downloadPath": None,
                            "url": "ftp://ftp.ensembl.org/pub/release-78/genbank/tursiops_truncatus/Tursiops_truncatus.turTru1.78.nonchromosomal.dat.gz"}
                            
        genbank_to_genome_http_img = {"external_type": "Genbank.Genome",
                            "kbase_type": "KBaseGenomes.Genome",
                            "object_name": "Fibrobacter_succinogenes_HM2_Project_1034376",
                            "filePath": None,
                            "downloadPath": None,
                            "url": "http://genome.jgi-psf.org/pages/dynamicOrganismDownload.jsf?organism=fibrobacteres#"}
        
        genbank_to_genome_gz = {"external_type": "Genbank.Genome",
                            "kbase_type": "KBaseGenomes.Genome",
                            "object_name": "NC_005213_gz",
                            "filePath": "data/NC_005213.gbk.gz",
                            "downloadPath": "NC_005213.gbk.gz"}

        genbank_to_genome_bz2 = {"external_type": "Genbank.Genome",
                             "kbase_type": "KBaseGenomes.Genome",
                             "object_name": "NC_005213_bz2",
                             "filePath": "data/NC_005213.gbk.bz2",
                             "downloadPath": "NC_005213.gbk.bz2"}

        genbank_to_genome_tar_bz2 = {"external_type": "Genbank.Genome",
                                 "kbase_type": "KBaseGenomes.Genome",
                                 "object_name": "NC_005213_tar_bz2",
                                 "filePath": "data/NC_005213.gbk.tar.bz2",
                                 "downloadPath": "NC_005213.gbk.tar.bz2"}

        genbank_to_genome_tar_gz = {"external_type": "Genbank.Genome",
                                "kbase_type": "KBaseGenomes.Genome",
                                "object_name": "NC_005213_tar_gz",
                                "filePath": "data/NC_005213.gbk.tar.gz",
                                "downloadPath": "NC_005213.gbk.tar.gz"}

        genbank_to_genome_zip = {"external_type": "Genbank.Genome",
                             "kbase_type": "KBaseGenomes.Genome",
                             "object_name": "NC_005213_zip",
                             "filePath": "data/NC_005213.gbk.zip",
                             "downloadPath": "NC_005213.gbk.zip"}

        fasta_to_reference = {"external_type": "FASTA.DNA.Assembly",
                          "kbase_type": "KBaseAssembly.ReferenceAssembly",
                          "object_name": "fasciculatum_supercontig",
                          "filePath": "data/fasciculatum_supercontig.fasta.zip",
                          "downloadPath": "fasciculatum_supercontig.fasta.zip"}

        fasta_single_to_reads = {"external_type": "FASTA.DNA.Reads",
                             "kbase_type": "KBaseAssembly.SingleEndLibrary",
                             "object_name": "ERR670568",
                             "filePath": "data/ERR670568.fasta.gz",
                             "downloadPath": "ERR670568.fasta.gz"}

        fastq_single_to_reads = {"external_type": "FASTQ.DNA.Reads",
                             "kbase_type": "KBaseAssembly.SingleEndLibrary",
                             "object_name": "ERR670568",
                             "filePath": "data/ERR670568.fastq.gz",
                             "downloadPath": "ERR670568.fastq.gz"}

        fasta_paired_to_reads = {"external_type": "FASTA.DNA.Reads",
                             "kbase_type": "KBaseAssembly.PairedEndLibrary",
                             "object_name": "SRR1569976",
                             "filePath": "data/SRR1569976.fasta.bz2",
                             "downloadPath": "SRR1569976.fasta.bz2"}

        fastq_paired1_to_reads = {"external_type": "FASTQ.DNA.Reads",
                              "kbase_type": "KBaseAssembly.PairedEndLibrary",
                              "object_name": "SRR1569976",
                              "filePath": "data/SRR1569976.fastq.bz2",
                              "downloadPath": "SRR1569976.fastq.bz2"}

        fastq_paired2_to_reads = {"external_type": "FASTQ.DNA.Reads",
                              "kbase_type": "KBaseAssembly.PairedEndLibrary",
                              "object_name": "SRR1569976_split",
                              "filePath": "data/SRR1569976_split.tar.bz2",
                              "downloadPath": "SRR1569976_split.tar.bz2"}

        sbml_to_fbamodel = {"external_type": "SBML.FBAModel",
                        "kbase_type": "KBaseFBA.FBAModel",
                        "object_name": "",
                        "filePath": "",
                        "downloadPath": ""}

        inputs = [fasta_to_contigset]
        
        #         genbank_to_genome,
        #         genbank_to_genome_ftp_ncbi_gz,
        #         genbank_to_genome_gz, 
        #         genbank_to_genome_bz2, 
        #         genbank_to_genome_tar_bz2, 
        #         genbank_to_genome_tar_gz, 
        #         genbank_to_genome_zip,
        #         genbank_to_genome_http_mol_zip,
        #         genbank_to_genome_ftp_patric,
        #         genbank_to_genome_ftp_refseq,
        #         genbank_to_genome_ftp_ensembl,
        #         genbank_to_genome_http_img,
        #         fasta_to_reference,
        #         fasta_to_contigset,
        #         fastq_single_to_reads, 
        #         fasta_single_to_reads, 
        #         fastq_single_to_reads, 
        #         fastq_paired1_to_reads, 
        #         fastq_paired2_to_reads, 
        #         fasta_paired_to_reads]
    

    services = {"shock": args.shock_service_url,
                "ujs": args.ujs_service_url,
                "workspace": args.workspace_service_url,
                "awe": args.awe_service_url,
                "transform": args.transform_service_url,
                "handle": args.handle_service_url}
    
    stamp = datetime.datetime.now().isoformat()
    os.mkdir(stamp)
    
    term = blessings.Terminal()
    for x in inputs:
        print x
        external_type = x["external_type"]
        kbase_type = x["kbase_type"]
        object_name = x["object_name"]
        filePath = x["filePath"]
        url_mapping = x["url_mapping"]

        print "\n\n"
        print term.bold("#"*80)
        print term.white_on_black("Converting {0} => {1}".format(external_type,kbase_type))
        print term.bold("#"*80)

        if x.has_key("url"):
            url = x["url"]

            try:
                print term.bright_blue("Uploading from remote http or ftp url")
                print term.bold("Step 1: Make KBase upload request with a url")
                print term.bold("Using data from : {0}".format(url))

                biokbase.Transform.script_utils.download_from_urls(logger, urls=url, shock_service_url=services["shock"], token=token)
                
                input_object = dict()
                input_object["external_type"] = external_type
                input_object["kbase_type"] = kbase_type
                input_object["url_mapping"] = dict()
                input_object["url_mapping"][url_mapping] =  url
                input_object["workspace_name"] = workspace
                input_object["object_name"] = object_name

                if args.handler_mode: 
                    print term.blue("\tTransform handler upload started:")
                    input_args = plugin.get_handler_args("upload",input_object, token)
                    command_list = ["trns_upload_taskrunner", "--working_directory", stamp ]
                    
                    for k in input_args:
                       command_list.append("--{0}".format(k))
                       command_list.append("{0}".format(input_args[k]))
                    for attr, value in args.__dict__.iteritems():
                       if attr.endswith("_service_url"):
                         command_list.append("--{0}".format(attr))
                         command_list.append("{0}".format(value))

                    task = subprocess.Popen(command_list, stderr=subprocess.PIPE)
                    sub_stdout, sub_stderr = task.communicate()
                
                    if sub_stdout is not None:
                        print sub_stdout
                    if sub_stderr is not None:
                        print >> sys.stderr, sub_stderr
                
                    if task.returncode != 0:
                        raise Exception(sub_stderr)
                else:
                    upload_response = upload(services["transform"], input_object, token)
                 
                    print term.blue("\tTransform service upload requested:")
                    print "\t\tConverting from {0} => {1}\n\t\tUsing workspace {2} with object name {3}".format(external_type,kbase_type,workspace,object_name)
                    print term.blue("\tTransform service responded with job ids:")
                    print "\t\tAWE job id {0}\n\t\tUJS job id {1}".format(upload_response[0], upload_response[1])
                 
                    show_job_progress(services["ujs"], services["awe"], upload_response[0], upload_response[1], token)

                print term.bold("Step 2: View or use workspace objects")
                show_workspace_object_list(services["workspace"], workspace, object_name, token)

                #show_workspace_object_contents(services["workspace"], workspace, object_name, token)
            except Exception, e:
                print e.message
                print e
        else:
            conversionDownloadPath = os.path.join(stamp, external_type + "_to_" + kbase_type)
            
            try:
                os.mkdir(conversionDownloadPath)
            except:
                pass
            
            downloadPath = os.path.join(conversionDownloadPath, x["downloadPath"])

            print term.bright_blue("Uploading local files")
            print term.bold("Step 1: Place local files in SHOCK")
            print term.blue("\tPreparing to upload {0}".format(filePath))
            print "\tFile size : {0:f} MB".format(int(os.path.getsize(filePath))/float(1024*1024))

            shock_response = post_to_shock(services["shock"], filePath, token)
            print term.green("\tShock upload of {0} successful.".format(filePath))
            print "\tShock id : {0}\n\n".format(shock_response['id'])
        
            print term.bold("Optional Step: Verify files uploaded to SHOCK\n")
            download_from_shock(services["shock"], shock_response["id"], downloadPath, token)
            print term.green("\tShock download of {0} successful.\n\n".format(downloadPath))

            try:
                print term.bold("Step 2: Make KBase upload request")

                input_object = dict()
                input_object["external_type"] = external_type
                input_object["kbase_type"] = kbase_type
                input_object["url_mapping"] = dict()
                input_object["url_mapping"][url_mapping] = "{0}/node/{1}".format(services["shock"],shock_response["id"])
                input_object["workspace_name"] = workspace
                input_object["object_name"] = object_name

                if args.handler_mode: 
                    print term.blue("\tTransform handler upload started:")
                    input_args = plugin.get_handler_args("upload",input_object, token)
                    command_list = ["trns_upload_taskrunner", "--working_directory", stamp ]
                    
                    for k in input_args:
                       command_list.append("--{0}".format(k))
                       command_list.append("{0}".format(input_args[k]))
                    for attr, value in args.__dict__.iteritems():
                       if attr.endswith("_service_url"):
                         command_list.append("--{0}".format(attr))
                         command_list.append("{0}".format(value))

                    task = subprocess.Popen(command_list, stderr=subprocess.PIPE)
                    sub_stdout, sub_stderr = task.communicate()
                
                    if sub_stdout is not None:
                        print sub_stdout
                    if sub_stderr is not None:
                        print >> sys.stderr, sub_stderr
                
                    if task.returncode != 0:
                        raise Exception(sub_stderr)
                       
                else:
                    upload_response = upload(services["transform"], input_object, token)
                    print term.blue("\tTransform service upload requested:")
                    print "\t\tConverting from {0} => {1}\n\t\tUsing workspace {2} with object name {3}".format(external_type,kbase_type,workspace,object_name)
                    print term.blue("\tTransform service responded with job ids:")
                    print "\t\tAWE job id {0}\n\t\tUJS job id {1}".format(upload_response[0], upload_response[1])
                 
                    show_job_progress(services["ujs"], services["awe"], upload_response[0], upload_response[1], token)
    
                print term.bold("Step 3: View or use workspace objects")
                show_workspace_object_list(services["workspace"], workspace, object_name, token)
    
                #show_workspace_object_contents(services["workspace"], workspace, object_name, token)
            except Exception, e:
                print e.message
                raise
