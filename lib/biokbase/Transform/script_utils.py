import sys
import logging
import time

import requests

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


def getHandles(logger,
               shock_url = "https://kbase.us/services/shock-api/",
               handle_url = "https://kbase.us/services/handle_service/",
               shock_ids = None,
               handle_ids = None,
               token = None):
    
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
                handle_id = hs.persist_handle({"id" : sid, 
                                           "type" : "shock",
                                           "url" : shock_url,
                                           "file_name": info["file"]["name"],
                                           "remote_md5": info["file"]["md5"]})
            except:
                try:
                    handle_id = hs.ids_to_handles([sid])[0]["hid"]
                    single_handle = hs.hids_to_handles([handle_id])
                
                    assert len(single_handle) != 0
                    
                    if info is not None:
                        single_handle[0]["file_name"] = info["file"]["name"]
                        single_handle[0]["remote_md5"] = info["file"]["md5"]
                        print >> sys.stderr, single_handle
                    
                    handles.append(single_handle[0])
                except:
                    logger.error("The input shock node id {} is already registered or could not be registered".format(sid))
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
