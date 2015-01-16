import sys
import os
import logging
import time
import re
import io
import gzip
import bz2
import tarfile
import zipfile

import magic
import requests
from requests_toolbelt import MultipartEncoder

from biokbase.AbstractHandle.Client import AbstractHandle


def getStderrLogger(name, level=logging.INFO):
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # send messages to sys.stderr
    streamHandler = logging.StreamHandler(sys.__stderr__)

    formatter = logging.Formatter("%(asctime)s - %(filename)s - %(lineno)d - %(levelname)s - %(message)s")
    formatter.converter = time.gmtime
    streamHandler.setFormatter(formatter)

    logger.addHandler(streamHandler)
    
    return logger



def extract_data(logger, filePath, chunkSize=10 * 2**20):
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



def download_file_from_shock(logger,
                             shock_service_url,
                             shock_id,
                             filePath,
                             token = None):

    header = dict()
    header["Authorization"] = "Oauth %s" % token

    print >> sys.stderr, "Downloading shock node"

    metadata_response = requests.get("{0}/node/{1}?verbosity=metadata".format(shock_service_url, shock_id), headers=header, stream=True, verify=True)
    shock_metadata = metadata_response.json()['data']
    fileName = shock_metadata['file']['name']
    fileSize = shock_metadata['file']['size']
    metadata_response.close()
        
    download_url = "{0}/node/{1}?download_raw".format(self.shock_url, shock_id)
        
    data = requests.get(download_url, headers=header, stream=True, verify=self.ssl_verify)
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
                             


def upload_file_to_shock(logger,
                         shock_service_url = "https://kbase.us/services/shock-api/",
                         filePath = None,
                         ssl_verify = True,
                         token = None):

    if token is None:
        raise Exception("Authentication token required!")
    
    #build the header
    header = dict()
    header["Authorization"] = "Oauth %s" % token

    if filePath is None:
        raise Exception("No file given for upload to SHOCK!")

    dataFile = io.open(os.path.abspath(filePath))
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


def getHandles(logger,
               shock_url = "https://kbase.us/services/shock-api/",
               handle_url = "https://kbase.us/services/handle_service/",
               shock_ids = None,
               handle_ids = None,
               token = None):
    
    if token is None:
        raise Exception("Authentication token required!")

    logger.debug(sys.path)
    logger.debug(token)
    logger.debug(handle_url)
    
    hs = AbstractHandle(url=handle_url, token=token)
    
    handles = list()
    if shock_ids is not None:
        header = dict()
        header["Authorization"] = "Oauth {0}".format(token)
        
        for sid in shock_ids:
            info = None
            
            try:
                logger.info("Found shock id {0}, retrieving information about the data.".format(sid))

                response = requests.get("{0}/node/{1}".format(shock_url, sid), headers=header, verify=True)
                info = response.json()["data"]
            except:
                logger.error("There was an error retrieving information about the shock node id {0} from url {1}".format(sid, shock_url))
            
            try:
                logger.info("Retrieving a handle id for the data.")
                handle = hs.persist_handle({"id" : sid, 
                                           "type" : "shock",
                                           "url" : shock_url,
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

                    hs = AbstractHandle(url=handle_url, token=token)
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
                                           "url" : shock_url,
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
