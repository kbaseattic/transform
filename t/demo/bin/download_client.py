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

import biokbase.Transform.Client
import biokbase.Transform.script_utils
import biokbase.userandjobstate.client
import biokbase.workspace.client

logger = biokbase.Transform.script_utils.stdoutlogger(__file__)


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
    error = ["error", "fail"]
    
    term = blessings.Terminal()

    header = dict()
    header["Authorization"] = "Oauth %s" % token

    print term.blue("\tUJS Job Status:")
    # wait for UJS to complete    
    last_status = ""
    time_limit = 30
    start = datetime.datetime.utcnow()
    while 1:        
        try:
            status = c.get_job_status(ujs_id)
        except Exception, e:
            print term.red("\t\tIssue connecting to UJS!")
            status[1] = "error"
            status[2] = "Caught Exception"
        
        if (datetime.datetime.utcnow() - start).seconds > time_limit:
            print "\t\tJob is taking longer than it should, check debugging messages for more information."
            status[1] = "error"
            status[2] = "Timeout"            
        
        if last_status != status[2]:
            print "\t\t{0} status update: {1}".format(status[0], status[2])
            last_status = status[2]
        
        if status[1] in completed:
            print term.green("\t\tKBase download completed!\n")
            return status, c.get_results(ujs_id)
        elif status[1] in error:
            print term.red("\t\tOur job failed!\n")
            
            print term.bold("Additional AWE job details for debugging")
            # check awe job output
            awe_details = requests.get("{0}/job/{1}".format(awe_url,awe_id), headers=header, verify=True)
            job_info = awe_details.json()["data"]
            print term.red(json.dumps(job_info, sort_keys=True, indent=4))
            
            awe_stdout = requests.get("{0}/work/{1}?report=stdout".format(awe_url,job_info["tasks"][0]["taskid"]+"_0"), headers=header, verify=True)
            print term.red("STDOUT : " + json.dumps(awe_stdout.json()["data"], sort_keys=True, indent=4))
            
            awe_stderr = requests.get("{0}/work/{1}?report=stderr".format(awe_url,job_info["tasks"][0]["taskid"]+"_0"), headers=header, verify=True)
            print term.red("STDERR : " + json.dumps(awe_stderr.json()["data"], sort_keys=True, indent=4))
            
            return status, None
    

def download(transform_url, options, token):
    c = biokbase.Transform.Client.Transform(url=transform_url, token=token)

    response = c.download(options)        
    return response


def download_from_shock(shockURL, shock_id, outPath, token):
    header = dict()
    header["Authorization"] = "Oauth {0}".format(token)

    metadata_response = requests.get("{0}/node/{1}?verbosity=metadata".format(shockURL, shock_id), headers=header, stream=True)
    shock_metadata = metadata_response.json()['data']
    filename = shock_metadata['file']['name']
    filesize = shock_metadata['file']['size']
    metadata_response.close()
    
    data = requests.get(shockURL + '/node/' + shock_id + "?download_raw", headers=header, stream=True)
    
    chunkSize = filesize/4
    download_iter = data.iter_content(chunkSize)

    outFile = os.path.join(outPath, filename)

    term = blessings.Terminal()
    f = open(outFile, 'wb')

    downloaded = 0
    try:
        for chunk in download_iter:
            f.write(chunk)
            
            if downloaded + chunkSize > filesize:
                downloaded = filesize
            else:
                downloaded += chunkSize
        
            print term.move_up + term.move_left + "\tDownloaded from shock {0:.2f}%".format(downloaded/float(filesize) * 100.0)
    except:
        raise        
    finally:
        f.close()
        data.close()
        
    print "\tFile size : {0:f} MB".format(int(os.path.getsize(outFile))/float(1024*1024))

    biokbase.Transform.script_utils.extract_data(logger, outFile)



if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='KBase Download demo and client')
    parser.add_argument('--demo', action="store_true")
    parser.add_argument('--ujs_service_url', nargs='?', help='UserandJobState service for monitoring progress', const="", default="https://kbase.us/services/userandjobstate/")
    parser.add_argument('--workspace_service_url', nargs='?', help='Workspace service for KBase objects', const="", default="https://kbase.us/services/ws/")
    parser.add_argument('--awe_service_url', nargs='?', help='AWE service for additional job monitoring', const="", default="http://140.221.67.242:7080")
    parser.add_argument('--transform_service_url', nargs='?', help='Transform service that handles the data conversion to KBase', const="", default="http://140.221.67.242:7778/")

    parser.add_argument('--external_type', nargs='?', help='the external type of the data', const="", default="")
    parser.add_argument('--kbase_type', nargs='?', help='the kbase object type to create', const="", default="")
    parser.add_argument('--workspace', nargs='?', help='name of the workspace where your objects should be created', const="", default="upload_testing")
    parser.add_argument('--object_name', nargs='?', help='name of the workspace object to create', const="", default="")
    parser.add_argument('--download_path', nargs='?', help='path to place downloaded files for validation', const=".", default=".")

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

    if not args.demo:
        user_inputs = {"external_type": args.external_type,
                       "kbase_type": args.kbase_type,
                       "object_name": args.object_name,
                       "downloadPath": args.download_path,
                       "workspace_name": args.workspace}

        workspace = args.workspace    
        inputs = [user_inputs]
    else:
        if "kbasetest" not in token and len(args.workspace.strip()) == 0:
            print "If you are running the demo as a different user than kbasetest, you need to provide the name of your workspace with --workspace."
            sys.exit(0)
        else:
            if args.workspace is not None:
                workspace = args.workspace

        single_reads_to_fasta = {"external_type": "SequenceReads",
                                 "kbase_type": "KBaseAssembly.SingleEndLibrary",
                                 "object_name": "ERR670568",
                                 "optional_arguments": {"transform": {"output_file_name": "ERR670568.fastq"}}
                                }

        contigset_to_fasta = {"external_type": "FASTA.DNA.Assembly",
                              "kbase_type": "KBaseGenomes.ContigSet",
                              "object_name": "fasciculatum_supercontig",
                              "optional_arguments": {"transform": {"output_file_name": "fs.fasta"}}
                             }

        genome_to_genbank = {"external_type": "Genbank.Genome",
                             "kbase_type": "KBaseGenomes.Genome",
                             "object_name": "NC_005213",
                             "optional_arguments": {"transform": {}}
                            }

        model_to_csv = {"external_type": "CSV.FBAModel",
                        "kbase_type": "KBaseFBA.FBAModel",
                        "object_name": "kb|g.131.model",
                        "workspace_name": "KBasePublicModelsV4",
                        "optional_arguments": {"transform": {}}
                       }

        model_to_sbml = {"external_type": "SBML.FBAModel",
                         "kbase_type": "KBaseFBA.FBAModel",
                         "object_name": "kb|g.131.model",
                         "workspace_name": "KBasePublicModelsV4",
                         "optional_arguments": {"transform": {}}
                       }

        inputs = [
                  model_to_sbml
                 ]
    

    services = {"ujs": args.ujs_service_url,
                "workspace": args.workspace_service_url,
                "awe": args.awe_service_url,
                "transform": args.transform_service_url}

    
    stamp = datetime.datetime.now().isoformat()
    os.mkdir(stamp)
    
    term = blessings.Terminal()
    for x in inputs:
        external_type = x["external_type"]
        kbase_type = x["kbase_type"]
        object_name = x["object_name"]
        
        if x.has_key("workspace_name") and x["workspace_name"]:
            ws_name = x["workspace_name"]
        else:
            ws_name = workspace

        optional_arguments = None
        if x.has_key("optional_arguments"):
            optional_arguments = x["optional_arguments"]

        print "\n\n"
        print term.bold("#"*80)
        print term.white_on_black("Converting {0} => {1}".format(kbase_type,external_type))
        print term.bold("#"*80)

        conversionDownloadPath = os.path.join(stamp, kbase_type + "_to_" + external_type)
        try:
            os.mkdir(conversionDownloadPath)
        except:
            pass
        
        downloadPath = os.path.join(conversionDownloadPath)

        try:
            print term.bold("Step 1: Make KBase download request")

            input_object = dict()
            input_object["external_type"] = external_type
            input_object["kbase_type"] = kbase_type
            input_object["workspace_name"] = ws_name
            input_object["object_name"] = object_name

            if optional_arguments is not None:
                input_object["optional_arguments"] = optional_arguments
            else:
                input_object["optional_arguments"] = {'transform': {}}

            download_response = download(services["transform"], input_object, token)
            print term.blue("\tTransform service download requested:")
            print "\t\tConverting from {0} => {1}\n\t\tUsing workspace {2} with object name {3}".format(kbase_type,external_type,workspace,object_name)
            print term.blue("\tTransform service responded with job ids:")
            print "\t\tAWE job id {0}\n\t\tUJS job id {1}".format(download_response[0], download_response[1])
         
            status, results = show_job_progress(services["ujs"], services["awe"], download_response[0], download_response[1], token)
            
            print term.bold("Step 2: Grab data from SHOCK\n")
            download_from_shock(results["shockurl"], results["results"][0]["id"], downloadPath, token)
            
            print term.green("\tShock download of {0} successful.\n\n".format(downloadPath))
        except Exception, e:
            print e.message

