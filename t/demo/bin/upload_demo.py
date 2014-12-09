#!/usr/bin/env python

import sys
import time
import os
import os.path
import io
import bz2
import gzip
import zipfile
import tarfile

sys.path.append(os.path.abspath("venv/lib/python2.7/site-packages/"))

from requests_toolbelt import MultipartEncoder, MultipartEncoderMonitor
import requests
import magic
import blessings

import biokbase.Transform.Client
import biokbase.userandjobstate.client
import biokbase.workspace.client


token = os.environ.get("KB_AUTH_TOKEN")
if token is None:
    raise Exception("Unable to find KBase token!")


def show_workspace_object_list(workspace_url, workspace_name):
    print "\tYour KBase data objects:"
    
    c = biokbase.workspace.client.Workspace(workspace_url, token=token)
    object_list = c.list_objects({"workspaces": [workspace_name]})
    
    for x in sorted(object_list):
        print "\t\t{0:30}{1:20}{2:>16}".format(x[1], x[2], x[-2])


def show_workspace_object_contents(workspace_url, workspace_name, object_name):
    c = biokbase.workspace.client.Workspace(workspace_url, token=token)
    object_contents = c.get_objects([{"workspace": workspace_name, "objid": 2}])
    print object_contents


def show_job_progress(ujs_url, awe_id, ujs_id):
    c = biokbase.userandjobstate.client.UserAndJobState(url=ujs_url, token=token)

    completed = ["complete", "success"]
    error = ["error", "fail"]
    
    term = blessings.Terminal()

    print "\tUJS Job Status:"
    
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
    
        #time.sleep(1)
    

def upload(transform_url, options):
    c = biokbase.Transform.Client.Transform(url=transform_url, token=token)

    response = c.upload(options)        
    return response


def post_to_shock(shockURL, filePath):
    size = os.path.getsize(filePath)
    chunkSize = size/10
    markers = [x for x in xrange(chunkSize,size,chunkSize)]

    term = blessings.Terminal()
    
    print "\tShock upload status:\n"
    def progress_indicator(monitor):
        if monitor.bytes_read > size:
            pass            
        else:
            progress = int(monitor.bytes_read)/float(size) * 100.0

            for x in markers:
                if int(monitor.bytes_read) > x:
                    print term.move_up + term.move_left + "\t\tPercentage of bytes uploaded to shock {0:.2f}%".format(progress)                        
                    del markers[markers.index(x)]
                    

            
    #build the header
    header = dict()
    header["Authorization"] = "Oauth %s" % token

    dataFile = open(os.path.abspath(filePath))
    encoder = MultipartEncoder(fields={'upload': (os.path.split(filePath)[-1], dataFile)})
    header['Content-Type'] = encoder.content_type
    
    m = MultipartEncoderMonitor(encoder, progress_indicator)

    response = requests.post(shockURL + "/node", headers=header, data=m, allow_redirects=True, verify=False)
    
    if not response.ok:
        print response.raise_for_status()

    result = response.json()

    print "Uploaded shock id : {}".format(result['data']['id'])

    if result['error']:
        raise Exception(result['error'][0])
    else:
        return result["data"]    


def download_from_shock(shockURL, shock_id, filePath):
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


    if mimeType == "application/x-gzip":
        print "\tExtracting {0} as gzip".format(filePath)
    
        with gzip.GzipFile(filePath, 'rb') as gzipDataFile, open(os.path.splitext(filePath)[0], 'wb') as f:
            for chunk in gzipDataFile:
                f.write(gzipDataFile.read(chunkSize))
        
        os.remove(filePath)
        print "\tExtracted File size : {0:f} MB".format(int(os.path.getsize(os.path.splitext(filePath)[0]))/float(1024*1024))        
    elif mimeType == "application/x-bzip2":
        print "\tExtracting {0} as bz2".format(filePath)
        
        with bz2.BZ2File(filePath, 'r') as bz2DataFile, open(os.path.splitext(filePath)[0], 'wb') as f:
            for chunk in bz2DataFile:
                f.write(bz2DataFile.read(chunkSize))
        
        os.remove(filePath)
        print "\tExtracted File size : {0:f} MB".format(int(os.path.getsize(os.path.splitext(filePath)[0]))/float(1024*1024))        
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
                infoPath = os.path.basename(os.path.abspath(x.filename))
                if os.path.exists(infoPath):
                    raise Exception("Extracting zip contents will overwrite an existing file!")
            
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
                memberPath = os.path.basename(os.path.abspath(member.name))
            
                if member.isfile():
                    print "\t\tExtracting {0:f} MB from {1} in {2}".format(int(member.size)/float(1024*1024),memberPath,filePath)
                    with open(memberPath, 'wb') as f, tarDataFile.extractfile(member.name) as inputFile:
                        f.write(inputFile.read(chunkSize))
        
        os.remove(filePath)






if __name__ == "__main__":
    services = {"shock": 'https://kbase.us/services/shock-api',
                "ujs": 'https://kbase.us/services/userandjobstate/',
                "workspace": 'http://kbase.us/services/ws',
                "awe": 'http://140.221.67.172:7080/',
                "transform": 'http://140.221.67.172:7778'}

    genbank_to_genome = {"external_type": "KBaseGenomes.GBK",
                         "kbase_type": "KBaseGenomes.Genome",
                         "workspace": "client_tests",
                         "object_name": "NC_005213",
                         "filePath": "data/genbank/NC_005213/NC_005213.gbk",
                         "downloadPath": "NC_005213.gbk"}

    fasta_reference_to_contigs = {"external_type": "KBaseAssembly.FA",
                                  "kbase_type": "KBaseAssembly.ReferenceAssembly",
                                  "workspace": "client_tests",
                                  "object_name": "fasciculatum_supercontig",
                                  "filePath": "data/fasciculatum_supercontig.fasta.zip",
                                  "downloadPath": "fasciculatum_supercontig.fasta.zip"}

    fasta_single_to_reads = {"external_type": "KBaseAssembly.FA",
                             "kbase_type": "KBaseAssembly.SingleEndLibrary",
                             "workspace": "client_tests",
                             "object_name": "ERR670568",
                             "filePath": "data/ERR670568.fasta.gz",
                             "downloadPath": "ERR670568.fasta.gz"}

    fastq_single_to_reads = {"external_type": "KBaseAssembly.FQ",
                             "kbase_type": "KBaseAssembly.SingleEndLibrary",
                             "workspace": "client_tests",
                             "object_name": "ERR670568",
                             "filePath": "data/ERR670568.fastq.gz",
                             "downloadPath": "ERR670568.fastq.gz"}

    fasta_paired_to_reads = {"external_type": "KBaseAssembly.FA",
                             "kbase_type": "KBaseAssembly.PairedEndLibrary",
                             "workspace": "client_tests",
                             "object_name": "SRR1569976",
                             "filePath": "data/SRR1569976.fasta.gz",
                             "downloadPath": "SRR1569976.fasta.gz"}

    fastq_paired_to_reads = {"external_type": "KBaseAssembly.FQ",
                             "kbase_type": "KBaseAssembly.PairedEndLibrary",
                             "workspace": "client_tests",
                             "object_name": "SRR1569976",
                             "filePath": "data/SRR1569976.fastq.gz",
                             "downloadPath": "SRR1569976.fastq.gz"}

    sbml_to_fbamodel = {"external_type": "KBaseFBA.SBML",
                        "kbase_type": "KBaseFBA.FBAModel",
                        "workspace": "client_tests",
                        "object_name": "",
                        "filePath": "",
                        "downloadPath": ""}

    demos = [genbank_to_genome, 
             fasta_reference_to_contigs,
             fastq_single_to_reads, 
             fasta_single_to_reads, 
             fastq_single_to_reads, 
             fasta_paired_to_reads, 
             fastq_paired_to_reads]

    import argparse

    parser = argparse.ArgumentParser(description='KBase Upload demo and client')
    parser.add_argument('--demo', action="store_true")
    parser.add_argument('--external_type', nargs='?', help='the external type of the data', const="", default="")
    parser.add_argument('--kbase_type', nargs='?', help='the kbase object type to create', const="", default="")
    parser.add_argument('--workspace', nargs='?', help='name of the workspace where your objects should be created', const="", default="")
    parser.add_argument('--object_name', nargs='?', help='name of the workspace object to create', const="", default="")
    parser.add_argument('--file_path', nargs='?', help='path to file for upload', const="", default="")
    parser.add_argument('--download_path', nargs='?', help='path to place downloaded files for validation', const=".", default=".")

    args = parser.parse_args()

    if not args.demo:
        user_inputs = {"external_type": args.external_type,
                       "kbase_type": args.kbase_type,
                       "workspace": args.workspace,
                       "object_name": args.object_name,
                       "filePath": args.file_path,
                       "downloadPath": args.download_path}
    
        demos = [user_inputs]
    
    term = blessings.Terminal()
    for demo_inputs in demos:
        external_type = demo_inputs["external_type"]
        kbase_type = demo_inputs["kbase_type"]
        workspace = demo_inputs["workspace"]
        object_name = demo_inputs["object_name"]
        filePath = demo_inputs["filePath"]
        downloadPath = demo_inputs["downloadPath"]

        print term.bold("Step 1: Place files in SHOCK (will soon accept any http or ftp url)")
        print "\tPreparing to upload {0}".format(filePath)
        print "\tFile size : {0:f} MB".format(int(os.path.getsize(filePath))/float(1024*1024))

        shock_response = post_to_shock(services["shock"], filePath)
        print "\tShock upload of {0} successful.\n\n".format(filePath)

        print term.bold("Optional Step: Verify files uploaded to SHOCK\n")
        download_from_shock(services["shock"], shock_response["id"], downloadPath)
        print "\tShock download of {0} successful.\n\n".format(downloadPath)

        print term.bold("Step 2: Make KBase upload request")
        upload_response = upload(services["transform"], {"etype": external_type, "kb_type": kbase_type, "in_id": shock_response["id"], "ws_name": workspace, "obj_name": object_name})
        print "\tTransform service upload requested:"
        print "\t\t Converting from {0} => {1}\n\t\t Using workspace {2} with object name {3}".format(external_type,kbase_type,workspace,object_name)
        print "\tTransform service responded with job ids:"
        print "\t\tAWE job id {0}\n\t\tUJS job id {1}".format(upload_response[0], upload_response[1])
    
        show_job_progress(services["ujs"], upload_response[0], upload_response[1])
    
        print term.bold("Step 3: View or use workspace objects")
        show_workspace_object_list(services["workspace"], workspace)
    
        #show_workspace_object_contents(services["workspace"], workspace, object_name)
        print "\n\n{0}\n{1}\n\n".format("#"*80,"#"*80)
