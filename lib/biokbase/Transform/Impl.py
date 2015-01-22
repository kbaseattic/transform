#BEGIN_HEADER
import sys
import os
import base64
import logging

import simplejson

#import pymemcache.client

from biokbase.workflow.KBW import run_async
import biokbase.log
#END_HEADER


class Transform:
    '''
    Module Name:
    Transform

    Module Description:
    Transform Service

This KBase service supports translations and transformations of data types,
including converting external file formats to KBase objects, 
converting KBase objects to external file formats, and converting KBase objects
to other KBase objects, either objects of different types or objects of the same
type but different versions.
    '''

    ######## WARNING FOR GEVENT USERS #######
    # Since asynchronous IO can lead to methods - even the same method -
    # interrupting each other, you must be *very* careful when using global
    # state. A method could easily clobber the state set by another while
    # the latter method is running.
    #########################################
    #BEGIN_CLASS_HEADER

    #def _get_memcache_client(self):
    #    try:
    #        client = pymemcache.client.Client(('localhost', 11211))
    #        return client
    #    except pymemcache.MemcacheClientError, e:
    #        raise
    #    except pymemcache.MemcacheUnknownCommandError, e:
    #        raise
    #    except pymemcache.MemcacheIllegalInputError, e:
    #        raise
    #    except pymemcache.MemcacheServerError, e:
    #        raise
    #    except pymemcache.MemcacheUnknownError, e:
    #        raise
    #    except pymemcache.MemcacheUnexpectedCloseError, e:
    #        raise


    def _run_job(self, method, ctx, args):
        if "optional_arguments" not in args:
            args["optional_arguments"] = '{}'

        # read local configuration
        #memcacheClient = self._get_memcache_client()

        args = self.pluginManager.get_handler_args(method, args)
        
        return run_async(self.config, ctx, args)

    #END_CLASS_HEADER

    # config contains contents of config file in a hash or None if it couldn't
    # be found
    def __init__(self, config):
        #BEGIN_CONSTRUCTOR
        self.config = config
        self.kbaseLogger = logging.getLogger('transform')
        #self.kbaseLogger.set_log_file('transform_service.log')

        pluginsDir = self.config["plugins_directory"]
        
        self.kbaseLogger.info("PLUGINS : " + str(plugins))
        
        self.pluginManager = handler_utils.Plugins(pluginsDir, logger=self.kbaseLogger)
        
        #END_CONSTRUCTOR
        pass

    def version(self, ctx):
        # ctx is the context object
        # return variables are: result
        #BEGIN version

        # get service config version        

        #END version

        # At some point might do deeper type checking...
        if not isinstance(result, basestring):
            raise ValueError('Method version return value ' +
                             'result is not type basestring as required.')
        # return the results
        return [result]

    def methods(self, ctx, query):
        # ctx is the context object
        # return variables are: results
        #BEGIN methods
        
        # pull method names

        #END methods

        # At some point might do deeper type checking...
        if not isinstance(results, list):
            raise ValueError('Method methods return value ' +
                             'results is not type list as required.')
        # return the results
        return [results]

    def upload(self, ctx, args):
        # ctx is the context object
        # return variables are: result
        #BEGIN upload
        self.kbaseLogger.log_message("DEBUG", "Calling upload")
        result = self._run_job("upload", ctx, args)
        #END upload

        # At some point might do deeper type checking...
        if not isinstance(result, list):
            raise ValueError('Method upload return value ' +
                             'result is not type list as required.')
        # return the results
        return [result]

    def download(self, ctx, args):
        # ctx is the context object
        # return variables are: result
        #BEGIN download
        result = self._run_job("download", ctx, args)
        #END download

        # At some point might do deeper type checking...
        if not isinstance(result, list):
            raise ValueError('Method download return value ' +
                             'result is not type list as required.')
        # return the results
        return [result]

    def convert(self, ctx, args):
        # ctx is the context object
        # return variables are: result
        #BEGIN convert
        result = self._run_job("convert", ctx, args)
        #END convert

        # At some point might do deeper type checking...
        if not isinstance(result, list):
            raise ValueError('Method convert return value ' +
                             'result is not type list as required.')
        # return the results
        return [result]
