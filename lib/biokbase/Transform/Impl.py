#BEGIN_HEADER
import sys
import os
import json

#import pymemcache.client

from biokbase.workflow.KBW import run_async
import biokbase.log
#END_HEADER


class Transform:
    '''
    Module Name:
    Transform

    Module Description:
    Transform APIs
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
        # sanity check on context and args objects
        #self.kbaseLogger.log_message("INFO", ctx)        
        #self.kbaseLogger.log_message("INFO", args)        

        if 'optional_args' not in args:
            args['optional_args'] = '{}'

        # read local configuration
        #memcacheClient = self._get_memcache_client()
        #args['mjob_details'] = memcacheClient.get(args['etype'] + ":" + args['kb_type'])

        #self.kbaseLogger.log_message("INFO", json.dumps(self.scripts_config, indent=4, sort_keys=True))

        job_details = dict()

        if self.scripts_config["config_map"]["validator"].has_key(args["etype"]):
            job_details["validator"] = self.scripts_config["config_map"]["validator"][args["etype"]]
            self.kbaseLogger.log_message("INFO", job_details["validator"])
        else:
            self.kbaseLogger.log_message("WARNING", "No validation available for {0} => {1}".format(args["etype"],args["kb_type"]))

        if self.scripts_config["config_map"]["transformer"].has_key(args["etype"] + "-to-" + args["kb_type"]):
            job_details["transformer"] = self.scripts_config["config_map"]["transformer"][args["etype"] + "-to-" + args["kb_type"]]
            self.kbaseLogger.log_message("INFO", job_details["transformer"])
        else:
            raise Exception("No conversion available for {0} => {1}".format(args["etype"],args["kb_type"]))

        if self.scripts_config["config_map"]["uploader"].has_key(args["kb_type"]):
            job_details["uploader"] = self.scripts_config["config_map"]["uploader"][args["kb_type"]]
            self.kbaseLogger.log_message("INFO", job_details["uploader"])
        else:
            pass
            #raise Exception("No upload available for {0} => {1}".format(args["etype"],args["kb_type"]))

        args["job_details"] = json.dumps(job_details)

        return run_async(self.config, ctx, args)

    #END_CLASS_HEADER

    # config contains contents of config file in a hash or None if it couldn't
    # be found
    def __init__(self, config):
        #BEGIN_CONSTRUCTOR
        self.config = config
        self.kbaseLogger = biokbase.log.log('transform')
        self.kbaseLogger.set_log_file('transform_service.log')

        #self.scripts_config = {"external_types": [],
        #                       "kbase_types": [],
        #                       "validate": {},
        #                       "upload": {},
        #                       "transform": {}}
        #pluginsDir = '/kb/deployment/services/Transform/plugins/'
        #plugins = os.listdir(pluginsDir)
        
        #for p in plugins:
        #    try:
        #        f = open(os.path.join(pluginsDir, p), 'r')
        #        pconfig = json.loads(f.read())
        #        f.close()
        #
        #        if "external_type" in pconfig:
        #            self.scripts_config["external_types"].append(pconfig["external_type"])
        #            self.scripts_config["transform"][pconfig["external_type"]] = pconfig["transform"]
        #        elif "kbase_type" in pconfig:
        #            self.scripts_config["kbase_types"].append(pconfig["kbase_type"])
        #            self.scripts_config["transform"][pconfig["kbase_type"]] = pconfig["transform"]
        #    except:
        #        self.kbaseLogger.log_message("WARNING", "Unable to read plugin {0}".format(p))

        f = open(self.config["scripts_config"], 'r')
        self.scripts_config = json.loads(f.read())
        f.close()

        #self.kbaseLogger.log_message("INFO", json.dumps(self.scripts_config, indent=4, sort_keys=True))        

        #END_CONSTRUCTOR
        pass

    
    def import_data(self, ctx, args):
        # ctx is the context object
        # return variables are: result
        #BEGIN import_data
        result = self._run_job("import", ctx, args)        
        #END import_data

        # At some point might do deeper type checking...
        if not isinstance(result, basestring):
            raise ValueError('Method import_data return value ' +
                             'result is not type basestring as required.')
        # return the results
        return [result]


    def validate(self, ctx, args):
        # ctx is the context object
        # return variables are: result
        #BEGIN validate
        result = self._run_job("validate", ctx, args)
        #END validate

        # At some point might do deeper type checking...
        if not isinstance(result, list):
            raise ValueError('Method validate return value ' +
                             'result is not type list as required.')
        # return the results
        return [result]


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


    def methods(self, ctx):
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


    def method_types(self, ctx, func):
        # ctx is the context object
        # return variables are: results
        #BEGIN method_types

        # pull method types

        #END method_types

        # At some point might do deeper type checking...
        if not isinstance(results, list):
            raise ValueError('Method method_types return value ' +
                             'results is not type list as required.')
        # return the results
        return [results]


    def method_config(self, ctx, func, type):
        # ctx is the context object
        # return variables are: result
        #BEGIN method_config

        # pull method configs

        #END method_config

        # At some point might do deeper type checking...
        if not isinstance(result, dict):
            raise ValueError('Method method_config return value ' +
                             'result is not type dict as required.')
        # return the results
        return [result]
