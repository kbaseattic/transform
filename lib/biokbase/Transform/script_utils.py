import sys
import os
import logging
import pydoc
import time
import re
import io
import gzip
import bz2
import tarfile
import zipfile

import simplejson
import magic
import ftputil
import requests
from requests_toolbelt import MultipartEncoder

try:
    from biokbase.HandleService.Client import HandleService 
except:
    from biokbase.AbstractHandle.Client import AbstractHandle as HandleService 

import biokbase.workspace.client


def stderrlogger(name, level=logging.INFO):
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # send messages to sys.stderr
    streamHandler = logging.StreamHandler(sys.stderr)

    formatter = logging.Formatter("%(asctime)s - %(filename)s - %(lineno)d - %(levelname)s - %(message)s")
    formatter.converter = time.gmtime
    streamHandler.setFormatter(formatter)

    logger.addHandler(streamHandler)
    
    return logger


def stdoutlogger(name, level=logging.INFO):
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # send messages to sys.stderr
    streamHandler = logging.StreamHandler(sys.stdout)

    formatter = logging.Formatter("%(asctime)s - %(filename)s - %(lineno)d - %(levelname)s - %(message)s")
    formatter.converter = time.gmtime
    streamHandler.setFormatter(formatter)

    logger.addHandler(streamHandler)
    
    return logger



def parse_docs(docstring=None):
    """Parses the docstring of a function and returns a dictionary of the elements."""

    # TODO, revisit this, probably can use other ways of doing this
    script_details = dict()
    
    keys = ["Authors","Returns","Args"]
    
    remainder = docstring[:]
    for k in keys:
        remainder, script_details[k] = remainder.split(k+":",1)
        script_details[k] = script_details[k].strip()

    script_details["Description"] = remainder
        
    # special treatment for Args since we want a dict, split on :, then cleanup whitespace
    # keep the : in the keys to do clean splits when getting the values
    argument_keys = [x.strip() for x in re.findall(".*:",script_details["Args"])]
        
    # split on the string in reverse by the keys, then wash out the extra whitespace
    remainder = script_details["Args"]
    argument_values = list()
    for k in reversed(argument_keys):
        remainder, value = remainder.split(k)        
        argument_values.append(" ".join([x.strip() for x in value.split("\n")]))
    
    # create the dict using they keys without :, then get the values in the correct order
    script_details["Args"] = dict(zip([x.replace(":","") for x in argument_keys], reversed(argument_values)))
    
    return script_details


def extract_data(logger = None, filePath = None, chunkSize=10 * 2**20):
    def extract_tar(tarPath):
        if not tarfile.is_tarfile(tarPath):
            raise Exception("Inavalid tar file " + tarPath)
    
        with tarfile.open(tarPath, 'r') as tarDataFile:
            memberlist = tarDataFile.getmembers()
        
            for member in memberlist:
                memberPath = os.path.join(os.path.dirname(os.path.abspath(tarPath)),os.path.basename(os.path.abspath(member.name)))
        
                if member.isfile():
                    with io.open(memberPath, 'wb') as f:
                        inputFile = tarDataFile.extractfile(member.name)
                        f.write(inputFile.read(chunkSize))
    
        os.remove(tarPath)

    mimeType = None    
    with magic.Magic(flags=magic.MAGIC_MIME_TYPE) as m:
        mimeType = m.id_filename(filePath)

    logger.info("Extracting {0} as {1}".format(filePath, mimeType))

    if mimeType == "application/x-gzip":
        outFile = os.path.splitext(filePath)[0]
        with gzip.GzipFile(filePath, 'rb') as gzipDataFile, io.open(outFile, 'wb') as f:
            for chunk in gzipDataFile:
                f.write(chunk)
        
        os.remove(filePath)
        outPath = os.path.dirname(filePath)

        # check for tar        
        with magic.Magic(flags=magic.MAGIC_MIME_TYPE) as m:
            mimeType = m.id_filename(outFile)

        if mimeType == "application/x-tar":
            logger.info("Extracting {0} as tar".format(outFile))
            extract_tar(outFile)
    elif mimeType == "application/x-bzip2":
        outFile = os.path.splitext(filePath)[0]
        with bz2.BZ2File(filePath, 'r') as bz2DataFile, io.open(outFile, 'wb') as f:
            for chunk in bz2DataFile:
                f.write(chunk)
        
        os.remove(filePath)
        outPath = os.path.dirname(filePath)

        # check for tar        
        with magic.Magic(flags=magic.MAGIC_MIME_TYPE) as m:
            mimeType = m.id_filename(outFile)

        if mimeType == "application/x-tar":
            logger.info("Extracting {0} as tar".format(outFile))
            extract_tar(outFile)
    elif mimeType == "application/zip":
        if not zipfile.is_zipfile(filePath):
            raise Exception("Invalid zip file!")                
        
        outPath = os.path.dirname(filePath)
        
        with zipfile.ZipFile(filePath, 'r') as zipDataFile:
            bad = zipDataFile.testzip()
        
            if bad is not None:
                raise Exception("Encountered a bad file in the zip : " + str(bad))
        
            infolist = zipDataFile.infolist()
        
            # perform sanity check on file names, extract each file individually
            for x in infolist:
                infoPath = os.path.join(outPath, os.path.basename(os.path.abspath(x.filename)))
                
                if not os.path.exists(os.path.dirname(infoPath)):
                    os.makedirs(infoPath)                    
                
                if os.path.exists(os.path.join(infoPath,os.path.split(x.filename)[-1])):
                    raise Exception("Extracting zip contents will overwrite an existing file!")
                
                with io.open(infoPath, 'wb') as f:
                    f.write(zipDataFile.read(x.filename))
        
        os.remove(filePath)
    elif mimeType == "application/x-gtar":
        if not tarfile.is_tarfile(filePath):
            raise Exception("Inavalid tar file " + filePath)

        outPath = os.path.dirname(filePath)

        with tarfile.open(filePath, 'r|*') as tarDataFile:
            memberlist = tarDataFile.getmembers()

            # perform sanity check on file names, extract each file individually
            for member in memberlist:
                memberPath = os.path.join(outPath, os.path.basename(os.path.abspath(member.name)))

                if os.path.exists(os.path.dirname(infoPath)):
                    os.makedirs(infoPath)                    

                if os.path.exists(os.path.join(infoPath,os.path.split(member.name)[-1])):
                    raise Exception("Extracting zip contents will overwrite an existing file!")

                if member.isfile():
                    with io.open(memberPath, 'wb') as f, tarDataFile.extractfile(member.name) as inputFile:
                        f.write(inputFile.read(chunkSize))

        os.remove(filePath)



def download_file_from_shock(logger = None,
                             shock_service_url = "https://kbase.us/services/shock-api/",
                             shock_id = None,
                             filePath = None,
                             token = None):

    header = dict()
    header["Authorization"] = "Oauth {0}".format(token)

    logger.info("Downloading shock node {0}/node/{1}".format(shock_service_url,shock_id))

    metadata_response = requests.get("{0}/node/{1}?verbosity=metadata".format(shock_service_url, shock_id), headers=header, stream=True, verify=True)
    shock_metadata = metadata_response.json()['data']
    fileName = shock_metadata['file']['name']
    fileSize = shock_metadata['file']['size']
    metadata_response.close()
        
    download_url = "{0}/node/{1}?download_raw".format(shock_service_url, shock_id)
        
    data = requests.get(download_url, headers=header, stream=True, verify=ssl_verify)
    size = int(data.headers['content-length'])

    filePath = os.path.join(filePath)

    f = io.open(filePath, 'wb')
    try:
        for chunk in data.iter_content(chunkSize):
            f.write(chunk)
    finally:
        data.close()
        f.close()      
    
    extract_data(filePath)
                             


def upload_file_to_shock(logger = None,
                         shock_service_url = "https://kbase.us/services/shock-api/",
                         filePath = None,
                         ssl_verify = True,
                         token = None):

    if token is None:
        raise Exception("Authentication token required!")
    
    #build the header
    header = dict()
    header["Authorization"] = "Oauth {0}".format(token)

    if filePath is None:
        raise Exception("No file given for upload to SHOCK!")

    dataFile = open(os.path.abspath(filePath), 'r')
    m = MultipartEncoder(fields={'upload': (os.path.split(filePath)[-1], dataFile)})
    header['Content-Type'] = m.content_type

    logger.info("Sending {0} to {1}".format(filePath,shock_service_url))
    try:
        response = requests.post(shock_service_url + "/node", headers=header, data=m, allow_redirects=True, verify=ssl_verify)
        dataFile.close()

        if not response.ok:
            response.raise_for_status()

        result = response.json()

        if result['error']:            
            raise Exception(result['error'][0])
        else:
            return result["data"]    
    except:
        dataFile.close()
        raise    


def getHandles(logger = None,
               shock_service_url = "https://kbase.us/services/shock-api/",
               handle_service_url = "https://kbase.us/services/handle_service/",
               shock_ids = None,
               handle_ids = None,
               token = None):
    
    if token is None:
        raise Exception("Authentication token required!")

    hs = HandleService(url=handle_service_url, token=token)
    
    handles = list()
    if shock_ids is not None:
        header = dict()
        header["Authorization"] = "Oauth {0}".format(token)
        
        for sid in shock_ids:
            info = None
            
            try:
                logger.info("Found shock id {0}, retrieving information about the data.".format(sid))

                response = requests.get("{0}/node/{1}".format(shock_service_url, sid), headers=header, verify=True)
                info = response.json()["data"]
            except:
                logger.error("There was an error retrieving information about the shock node id {0} from url {1}".format(sid, shock_service_url))
            
            try:
                logger.info("Retrieving a handle id for the data.")
                handle = hs.persist_handle({"id" : sid, 
                                           "type" : "shock",
                                           "url" : shock_service_url,
                                           "file_name": info["file"]["name"],
                                           "remote_md5": info["file"]["checksum"]["md5"]})
                handles.append(handle)
            except:
                try:
                    handle_id = hs.ids_to_handles([sid])[0]["hid"]
                    single_handle = hs.hids_to_handles([handle_id])
                
                    assert len(single_handle) != 0
                    
                    if info is not None:
                        single_handle[0]["file_name"] = info["file"]["name"]
                        single_handle[0]["remote_md5"] = info["file"]["checksum"]["md5"]
                        logger.debug(single_handle)
                    
                    handles.append(single_handle[0])
                except:
                    logger.error("The input shock node id {} is already registered or could not be registered".format(sid))

                    hs = HandleService(url=handle_service_url, token=token)
                    all_handles = hs.list_handles()

                    for x in all_handles:
                        if x[0] == sid:
                            logger.info("FOUND shock id as existing handle")
                            logger.info(x)
                            break
                    else:
                        logger.info("Unable to find a handle containing shock id")

                        logger.info("Trying again to get a handle id for the data.")
                        handle_id = hs.persist_handle({"id" : sid, 
                                           "type" : "shock",
                                           "url" : shock_service_url,
                                           "file_name": info["file"]["name"],
                                           "remote_md5": info["file"]["checksum"]["md5"]})
                        handles.append(handle_id)

                    raise
    elif handle_ids is not None:
        for hid in handle_ids:
            try:
                single_handle = hs.hids_to_handles([hid])

                assert len(single_handle) != 0
                
                handles.append(single_handle[0])
            except:
                logger.error("Invalid handle id {0}".format(hid))
                raise
    
    return handles


def download_from_urls(logger = None,
                       working_directory = os.getcwd(),
                       urls = None,
                       shock_service_url = "https://kbase.us/services/shock-api/",
                       ssl_verify = True,
                       token = None, 
                       chunkSize = 10 * 2**20):
    if token is None:
        raise Exception("Unable to find token!")
    
    if not os.path.exists(working_directory):
        os.mkdir(working_directory)
    elif not os.path.isdir(working_directory):
        raise Exception("Attempting to process downloads using a path that is not a directory!")

    if urls is None:
        raise Exception("No urls to upload from!")

    if type(urls) != type(dict()):
        raise Exception("Expected dictionary of urls, instead found {0}".format(type(urls)))
    
    assert len(urls.keys()) != 0

    for name, url in urls.items():
        data = None
        download_directory = os.path.join(working_directory, name)
        os.mkdir(download_directory)
        
        # detect url type
        if url.startswith("ftp://"):
            threshold=1024

            # check if file or directory
            host = url.split("ftp://")[1].split("/")[0]
            path = url.split("ftp://")[1].split("/", 1)[1]
        
            ftp_connection = ftputil.FTPHost(host, 'anonymous', 'anonymous@')
            
            if ftp_connection.path.isdir(path):
                file_list = ftp_connection.listdir(path)
            elif ftp_connection.path.isfile(path):
                file_list = [path]

            if len(file_list) > 1:            
                if len(file_list) > threshold:
                    raise Exception("Too many files to process, found so far {0:d}".format(len(file_list)))
                                                
                if len(path.split("/")[-1]) == 0:
                    dirname = os.path.join(download_directory, path.split("/")[-2])
                else:
                    dirname = os.path.join(download_directory, path.split("/")[-1])
            
                all_files = list()
                check = file_list[:]
                while len(check) > 0:
                    x = check.pop()
            
                    new_files = ftp_connection.listdir(x)
                
                    for n in new_files:
                        if ftp_connection.path.isfile(n):
                            all_files.append(n)
                        elif ftp_connection.path.isdir(n):
                            check.append(n)
                        if len(all_files) > threshold:
                            raise Exception("Too many files to process, found so far {0:d}".format(len(all_files)))
                
                os.mkdir(dirname)
        
                for x in all_files:
                    filePath = os.path.join(os.path.abspath(dirname), os.path.basename(x))
                    logger.info("Downloading {0}".format(host + x))
                    ftp_connection.download(x, filePath)
                    extract_data(logger, filePath)
            else:
                filePath = os.path.join(download_directory, os.path.split(path)[-1])
                logger.info("Downloading {0}".format(url))
                ftp_connection.download(path, filePath)
                extract_data(logger, filePath)
            
            ftp_connection.close()            
        elif url.startswith("http://") or url.startswith("https://"):
            logger.info("Downloading {0}".format(url))

            download_url = None
            fileSize = 0
            fileName = None

            header = dict()
            header["Authorization"] = "Oauth {0}".format(token)

            # check for a shock url
            try:
                shock_id = re.search('^http[s]://.*/node/([a-fA-f0-9\-]+).*', url).group(1)
                shock_download_url = re.search('^(http[s]://.*)/node/[a-fA-f0-9\-]+.*', url).group(1)
            except Exception, e:
                shock_id = None

            if shock_id is None:
                download_url = url
                fileName = url.split('/')[-1]
            else:
                metadata_response = requests.get("{0}/node/{1}?verbosity=metadata".format(shock_download_url, shock_id), headers=header, stream=True, verify=ssl_verify)
                shock_metadata = metadata_response.json()['data']
                fileName = shock_metadata['file']['name']
                fileSize = shock_metadata['file']['size']
                metadata_response.close()
                    
                download_url = "{0}/node/{1}?download_raw".format(shock_download_url, shock_id)

            data = None
            size = 0
            try:    
                data = requests.get(download_url, headers=header, stream=True, verify=ssl_verify)
                if 'content-length' in data.headers:
                    size = int(data.headers['content-length'])
                if 'content-disposition' in data.headers:
                    fileName = data.headers['content-disposition'].split("filename=")[-1].replace("\\","").replace("\"","")
            except Exception, e:
                raise

            if size > 0 and fileSize == 0:
                fileSize = size
            
            filePath = os.path.join(download_directory, fileName)

            logger.info("Writing out {0}".format(fileName))
            
            f = io.open(filePath, 'wb')
            try:
                for chunk in data.iter_content(chunkSize):
                    f.write(chunk)
            finally:
                data.close()
                f.close()      
            
            resultFile = extract_data(logger, filePath)
        else:
            raise Exception("Unrecognized protocol or url format : " + url)
    

            
            
def save_json_to_workspace(logger = None,
                           workspace_service_url = None,
                           json_file = None,
                           kbase_info_file = None,
                           object_details = None,
                           token = None):

    """
    Saves an object to a workspace given a JSON data file.
    
    TODO
    Optionally if this data was originally from KBase, a KBase info file can
    be given that will be saved to the workspace with the object.
    """

    f = open(json_file, 'r')
    data = simplejson.loads(f.read())
    f.close()
    
    workspaceClient = biokbase.workspace.client.Workspace(workspace_service_url, token=os.environ.get("KB_AUTH_TOKEN"))
    
    workspaceClient.save_objects({"workspace": object_details["workspace_name"],
                                  "objects": [{
                                      "type": object_details["kbase_type"],
                                      "data": data,
                                      "name": object_details["object_name"],
                                      "meta": object_details["object_meta"],
                                      "provenance": object_details["provenance"]}
                                  ]})
    
