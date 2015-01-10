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
import json
import pprint

sys.path.insert(0,os.path.abspath("venv/lib/python2.7/site-packages/"))

from requests_toolbelt import MultipartEncoder, MultipartEncoderMonitor
import requests
import magic
import blessings
import dateutil.parser
import dateutil.tz

import biokbase.Transform.Client
import biokbase.userandjobstate.client
import biokbase.workspace.client


def show_workspace_object_list(workspace_url, workspace_name, object_name, token):
    print "\tYour KBase data objects:"
    
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
    error = ["error", "fail"]
    
    term = blessings.Terminal()

    header = dict()
    header["Authorization"] = "Oauth %s" % token

    print "\tUJS Job Status:"
    # wait for UJS to complete    
    last_status = ""
    while 1:
        status = c.get_job_status(ujs_id)
        
        if last_status != status[2]:
            print "\t\t{0} status update: {1}".format(status[0], status[2])
            last_status = status[2]
        
        if status[1] in completed:
            print term.green("\t\tKBase upload completed!\n")
            break
        elif status[1] in error:
            print term.red("\t\tOur job failed!\n")
            break
    

def upload(transform_url, options, token):
    c = biokbase.Transform.Client.Transform(url=transform_url, token=token)

    response = c.upload(options)        
    return response


def post_to_shock(shockURL, filePath, token):
    size = os.path.getsize(filePath)

    term = blessings.Terminal()
    
    print "\tShock upload status:\n"
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

    mimeType = None    
    with magic.Magic(flags=magic.MAGIC_MIME_TYPE) as m:
        mimeType = m.id_filename(filePath)

    print "Detected as mimetype {0}".format(mimeType)

    if mimeType == "application/x-gzip":
        print "\tExtracting {0} as gzip".format(filePath)
    
        with gzip.GzipFile(filePath, 'rb') as gzipDataFile, open(os.path.splitext(filePath)[0], 'wb') as f:
            for chunk in gzipDataFile:
                f.write(chunk)
        
        os.remove(filePath)
        print "\tExtracted File size : {0:f} MB".format(int(os.path.getsize(os.path.splitext(filePath)[0]))/float(1024*1024))        
    elif mimeType == "application/x-bzip2":
        print "\tExtracting {0} as bz2".format(filePath)
        
        outPath = os.path.splitext(filePath)[0]
        
        with bz2.BZ2File(filePath, 'r') as bz2DataFile, open(outPath, 'wb') as f:
            for chunk in bz2DataFile:
                f.write(chunk)
        
        os.remove(filePath)
        print "\tExtracted File size : {0:f} MB".format(int(os.path.getsize(outPath))/float(1024*1024))
        
        # check for tar        
        with magic.Magic(flags=magic.MAGIC_MIME_TYPE) as m:
            mimeType = m.id_filename(outPath)

        if mimeType == "application/x-tar":
            print "Extracting {0} as tar".format(outPath)
        
            if not tarfile.is_tarfile(outPath):
                raise Exception("Inavalid tar file " + outPath)
        
            with tarfile.open(outPath, 'r') as tarDataFile:
                memberlist = tarDataFile.getmembers()
            
                for member in memberlist:
                    memberPath = os.path.join(os.path.dirname(os.path.abspath(outPath)),os.path.basename(os.path.abspath(member.name)))
            
                    if member.isfile():
                        print "\t\tExtracting {0:f} MB from {1} in {2}".format(int(member.size)/float(1024*1024),memberPath,outPath)
                        with open(memberPath, 'wb') as f:
                            inputFile = tarDataFile.extractfile(member.name)
                            f.write(inputFile.read(chunkSize))
        
            os.remove(outPath)
    elif mimeType == "application/zip":
        print "\tExtracting {0} as zip".format(filePath)
        
        if not zipfile.is_zipfile(filePath):
            raise Exception("Invalid zip file!")                
        
        with zipfile.ZipFile(filePath, 'r') as zipDataFile:
            bad = zipDataFile.testzip()
        
            if bad is not None:
                raise Exception("Encountered a bad file in the zip : " + str(bad))
        
            infolist = zipDataFile.infolist()
        
            for x in infolist:
                infoPath = os.path.join(os.path.dirname(filePath), os.path.basename(os.path.abspath(x.filename)))

                #if os.path.exists(infoPath):
                #    raise Exception("Extracting zip contents will overwrite an existing file!")
            
                print "\t\tExtracting {0:f} MB from {1} in {2}".format(int(x.file_size)/float(1024*1024),infoPath,filePath)
                with open(infoPath, 'wb') as f:
                    f.write(zipDataFile.read(x.filename))
        
        os.remove(filePath)        
    elif mimeType == "application/x-gtar":
        print "Extracting {0} as tar".format(filePath)
        
        if not tarfile.is_tarfile(filePath):
            raise Exception("Inavalid tar file " + filePath)
        
        with tarfile.open(filePath, 'r|*') as tarDataFile:
            memberlist = tarDataFile.getmembers()
            
            for member in memberlist:
                memberPath = os.path.join(os.path.dirname(filePath),os.path.basename(os.path.abspath(member.name)))
            
                if member.isfile():
                    print "\t\tExtracting {0:f} MB from {1} in {2}".format(int(member.size)/float(1024*1024),memberPath,filePath)
                    with open(memberPath, 'wb') as f, tarDataFile.extractfile(member.name) as inputFile:
                        f.write(inputFile.read(chunkSize))
        
        os.remove(filePath)




if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='KBase Upload demo and client')
    parser.add_argument('--demo', action="store_true")
    parser.add_argument('--external_type', nargs='?', help='the external type of the data', const="", default="")
    parser.add_argument('--kbase_type', nargs='?', help='the kbase object type to create', const="", default="")
    parser.add_argument('--workspace', nargs='?', help='name of the workspace where your objects should be created', const="", default="upload_testing")
    parser.add_argument('--object_name', nargs='?', help='name of the workspace object to create', const="", default="")
    parser.add_argument('--file_path', nargs='?', help='path to file for upload', const="", default="")
    parser.add_argument('--download_path', nargs='?', help='path to place downloaded files for validation', const=".", default=".")

    args = parser.parse_args()

    if not args.demo:
        user_inputs = {"external_type": args.external_type,
                       "kbase_type": args.kbase_type,
                       "object_name": args.object_name,
                       "filePath": args.file_path,
                       "downloadPath": args.download_path}

        workspace = args.workspace    
        demos = [user_inputs]
    else:
        if "kbasetest" not in token and len(args.workspace.strip()) == 0:
            print "If you are running the demo as a different user than kbasetest, you need to provide the name of your workspace with --workspace."
            sys.exit(0)
        else:
            if args.workspace is not None:
                workspace = args.workspace

        genbank_to_genome = {"external_type": "KBaseGenomes.GBK",
                         "kbase_type": "KBaseGenomes.Genome",
                         "object_name": "NC_005213",
                         "filePath": "data/genbank/NC_005213/NC_005213.gbk",
                         "downloadPath": "NC_005213.gbk"}

        genbank_to_genome_gz = {"external_type": "KBaseGenomes.GBK",
                            "kbase_type": "KBaseGenomes.Genome",
                            "object_name": "NC_005213_gz",
                            "filePath": "data/NC_005213.gbk.gz",
                            "downloadPath": "NC_005213.gbk.gz"}

        genbank_to_genome_bz2 = {"external_type": "KBaseGenomes.GBK",
                             "kbase_type": "KBaseGenomes.Genome",
                             "object_name": "NC_005213_bz2",
                             "filePath": "data/NC_005213.gbk.bz2",
                             "downloadPath": "NC_005213.gbk.bz2"}

        genbank_to_genome_tar_bz2 = {"external_type": "KBaseGenomes.GBK",
                                 "kbase_type": "KBaseGenomes.Genome",
                                 "object_name": "NC_005213_tar_bz2",
                                 "filePath": "data/NC_005213.gbk.tar.bz2",
                                 "downloadPath": "NC_005213.gbk.tar.bz2"}

        genbank_to_genome_tar_gz = {"external_type": "KBaseGenomes.GBK",
                                "kbase_type": "KBaseGenomes.Genome",
                                "object_name": "NC_005213_tar_gz",
                                "filePath": "data/NC_005213.gbk.tar.gz",
                                "downloadPath": "NC_005213.gbk.tar.gz"}

        genbank_to_genome_zip = {"external_type": "KBaseGenomes.GBK",
                             "kbase_type": "KBaseGenomes.Genome",
                             "object_name": "NC_005213_zip",
                             "filePath": "data/NC_005213.gbk.zip",
                             "downloadPath": "NC_005213.gbk.zip"}

        fasta_to_reference = {"external_type": "KBaseAssembly.FA",
                          "kbase_type": "KBaseAssembly.ReferenceAssembly",
                          "object_name": "fasciculatum_supercontig",
                          "filePath": "data/fasciculatum_supercontig.fasta.zip",
                          "downloadPath": "fasciculatum_supercontig.fasta.zip"}

        fasta_to_contigset = {"external_type": "Assembly.FASTA",
                          "kbase_type": "KBaseGenomes.ContigSet",
                          "object_name": "fasciculatum_supercontig",
                          "filePath": "data/fasciculatum_supercontig.fasta.zip",
                          "downloadPath": "fasciculatum_supercontig.fasta.zip"}

        fasta_single_to_reads = {"external_type": "KBaseAssembly.FA",
                             "kbase_type": "KBaseAssembly.SingleEndLibrary",
                             "object_name": "ERR670568",
                             "filePath": "data/ERR670568.fasta.gz",
                             "downloadPath": "ERR670568.fasta.gz"}

        fastq_single_to_reads = {"external_type": "KBaseAssembly.FQ",
                             "kbase_type": "KBaseAssembly.SingleEndLibrary",
                             "object_name": "ERR670568",
                             "filePath": "data/ERR670568.fastq.gz",
                             "downloadPath": "ERR670568.fastq.gz"}

        fasta_paired_to_reads = {"external_type": "KBaseAssembly.FA",
                             "kbase_type": "KBaseAssembly.PairedEndLibrary",
                             "object_name": "SRR1569976",
                             "filePath": "data/SRR1569976.fasta.bz2",
                             "downloadPath": "SRR1569976.fasta.bz2"}

        fastq_paired1_to_reads = {"external_type": "KBaseAssembly.FQ",
                              "kbase_type": "KBaseAssembly.PairedEndLibrary",
                              "object_name": "SRR1569976",
                              "filePath": "data/SRR1569976.fastq.bz2",
                              "downloadPath": "SRR1569976.fastq.bz2"}

        fastq_paired2_to_reads = {"external_type": "KBaseAssembly.FQ",
                              "kbase_type": "KBaseAssembly.PairedEndLibrary",
                              "object_name": "SRR1569976_split",
                              "filePath": "data/SRR1569976_split.tar.bz2",
                              "downloadPath": "SRR1569976_split.tar.bz2"}

        sbml_to_fbamodel = {"external_type": "KBaseFBA.SBML",
                        "kbase_type": "KBaseFBA.FBAModel",
                        "object_name": "",
                        "filePath": "",
                        "downloadPath": ""}

        demos = [genbank_to_genome,
             genbank_to_genome_gz, 
             genbank_to_genome_bz2, 
             genbank_to_genome_tar_bz2, 
             genbank_to_genome_tar_gz, 
             genbank_to_genome_zip, 
             fasta_to_reference,
             fasta_to_contigset,
             fastq_single_to_reads, 
             fasta_single_to_reads, 
             fastq_single_to_reads, 
             fastq_paired1_to_reads, 
             fastq_paired2_to_reads, 
             fasta_paired_to_reads]
    

    services = {"shock": 'https://kbase.us/services/shock-api/',
                "ujs": 'https://kbase.us/services/userandjobstate/',
                "workspace": 'https://kbase.us/services/ws/',
                "awe": 'http://140.221.67.172:7080/',
                "transform": 'http://140.221.67.172:7778/'}

    token = os.environ.get("KB_AUTH_TOKEN")
    if token is None:
        if os.path.exists("~/.kbase_config"):
            f = open("~/.kbase_config", 'r')
            config = f.read()
            if "token=" in config:
                token = config.split("token=")[1].split("\n",1)[0]            
            else:
                raise Exception("Unable to find KBase token!")
        else:
            raise Exception("Unable to find KBase token!")
    
    stamp = datetime.datetime.now().isoformat()
    os.mkdir(stamp)
    
    term = blessings.Terminal()
    for demo_inputs in demos:
        external_type = demo_inputs["external_type"]
        kbase_type = demo_inputs["kbase_type"]
        object_name = demo_inputs["object_name"]
        filePath = demo_inputs["filePath"]

        conversionDownloadPath = os.path.join(stamp, external_type + "_to_" + kbase_type)
        try:
            os.mkdir(conversionDownloadPath)
        except:
            pass
        downloadPath = os.path.join(conversionDownloadPath, demo_inputs["downloadPath"])

        print "\n\n{0}\nConverting {1} => {2}\n{3}\n\n".format("#"*80,external_type,kbase_type,"#"*80)

        print term.bold("Step 1: Place files in SHOCK (will soon accept any http or ftp url)")
        print "\tPreparing to upload {0}".format(filePath)
        print "\tFile size : {0:f} MB".format(int(os.path.getsize(filePath))/float(1024*1024))

        shock_response = post_to_shock(services["shock"], filePath, token)
        print "\tShock upload of {0} successful.".format(filePath)
        print "\tShock id : {0}\n\n".format(shock_response['id'])
        
        print term.bold("Optional Step: Verify files uploaded to SHOCK\n")
        download_from_shock(services["shock"], shock_response["id"], downloadPath, token)
        print "\tShock download of {0} successful.\n\n".format(downloadPath)

        print term.bold("Step 2: Make KBase upload request")
        upload_response = upload(services["transform"], {"etype": external_type, "kb_type": kbase_type, "in_id": "{0}/node/{1}".format(services["shock"],shock_response["id"]), "ws_name": workspace, "obj_name": object_name}, token)
        print "\tTransform service upload requested:"
        print "\t\tConverting from {0} => {1}\n\t\tUsing workspace {2} with object name {3}".format(external_type,kbase_type,workspace,object_name)
        print "\tTransform service responded with job ids:"
        print "\t\tAWE job id {0}\n\t\tUJS job id {1}".format(upload_response[0], upload_response[1])
    
        show_job_progress(services["ujs"], services["awe"], upload_response[0], upload_response[1], token)
    
        print term.bold("Step 3: View or use workspace objects")
        show_workspace_object_list(services["workspace"], workspace, object_name, token)
    
        #show_workspace_object_contents(services["workspace"], workspace, object_name, token)
