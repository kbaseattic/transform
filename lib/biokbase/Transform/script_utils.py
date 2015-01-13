import sys
import logging
import time

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


def getShockID(logger,
               shock_service_url = "https://kbase.us/services/shock-api/",
               filePath = None,
               token = None):

    if token is None:
        raise Exception("Authentication token required!")
    
    #build the header
    header = dict()
    header["Authorization"] = "Oauth %s" % token

    if filePath is None:
        raise Exception("No file given for upload to SHOCK!")

    dataFile = open(os.path.abspath(filePath))
    m = MultipartEncoder(fields={'upload': (os.path.split(filePath)[-1], dataFile)})
    header['Content-Type'] = m.content_type

    logger.info("Sending {0} to {1}".format(filePath,shock_service_url))
    try:
        response = requests.post(shock_service_url + "/node", headers=header, data=m, allow_redirects=True, verify=True)
        dataFile.close()

        if not response.ok:
            response.raise_for_status()

        result = response.json()

        if result['error']:            
            raise Exception(result['error'][0])
        else:
            return result["data"]["id"]    
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
