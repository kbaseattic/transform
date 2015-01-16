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
        # sanity check on context and args objects
        #self.kbaseLogger.log_message("INFO", ctx)        
        #self.kbaseLogger.log_message("INFO", args)        

        if 'optional_arguments' not in args:
            args['optional_arguments'] = '{}'

        # read local configuration
        #memcacheClient = self._get_memcache_client()
        #args['mjob_details'] = memcacheClient.get(args['etype'] + ":" + args['kb_type'])

        #self.kbaseLogger.log_message("INFO", json.dumps(self.scripts_config, indent=4, sort_keys=True))

        job_details = dict()

        if self.scripts_config["validate"].has_key(args["external_type"]):
            job_details["validator"] = self.scripts_config["validate"][args["external_type"]]
        else:
            self.kbaseLogger.log_message("WARNING", "No validation available for {0}".format(args["external_type"]))

        if self.scripts_config["transform." + method].has_key("{0}=>{1}".format(args["external_type"],args["kbase_type"])):
            job_details["transformer"] = self.scripts_config["transform." + method]["{0}=>{1}".format(args["external_type"],args["kbase_type"])]
        else:
            raise Exception("No conversion available for {0} => {1}".format(args["external_type"],args["kbase_type"]))

        if self.scripts_config["uploader"].has_key(args["kbase_type"]):
            job_details["uploader"] = self.scripts_config["upload"][args["kbase_type"]]
        else:
            pass
            #raise Exception("No upload available for {0} => {1}".format(args["etype"],args["kb_type"]))

        args["job_details"] = json.dumps(job_details)

        self.kbaseLogger.log_message("INFO", "Invoking {0} with ({1},{2})".format(method,str(ctx),str(args)))
        
        return run_async(self.config, ctx, args)

    #END_CLASS_HEADER

    # config contains contents of config file in a hash or None if it couldn't
    # be found
    def __init__(self, config):
        #BEGIN_CONSTRUCTOR
        self.config = config
        self.kbaseLogger = biokbase.log.log('transform')
        self.kbaseLogger.set_log_file('transform_service.log')

        self.scripts_config = {"external_types": set(),
                               "kbase_types": set(),
                               "validate": dict(),
                               "transform.upload": dict(),
                               "transform.download": dict(),
                               "convert": dict()}
        pluginsDir = 'plugins/configs'
        plugins = os.listdir(pluginsDir)
        
        for p in plugins:
            try:
                f = open(os.path.join(pluginsDir, p), 'r')
                pconfig = json.loads(f.read())
                f.close()

                self.kbaseLogger.log_message("INFO", json.dumps(pconfig, indent=4, sort_keys=True))        

                if pconfig["script_type"].startswith("transform"):
                    self.scripts_config["external_types"].add(pconfig["external_type"])
                    self.scripts_config["kbase_types"].add(pconfig["kbase_type"])

                id = None

                if pconfig["script_type"] == "validate":
                    self.scripts_config["external_types"].add(pconfig["external_type"])
                    id = pconfig["external_type"]
                elif pconfig["script_type"] == "transform.upload":
                    self.scripts_config["external_types"].add(pconfig["external_type"])
                    self.scripts_config["kbase_types"].add(pconfig["kbase_type"])
                    id = "{0}=>{1}".format(pconfig["external_type"],pconfig["kbase_type"])
                elif pconfig["script_type"] == "transform.download":
                    self.scripts_config["external_types"].add(pconfig["external_type"])
                    self.scripts_config["kbase_types"].add(pconfig["kbase_type"])
                    id = "{0}=>{1}".format(pconfig["kbase_type"],pconfig["external_type"])
                elif pconfig["script_type"] == "convert":
                    self.scripts_config["kbase_types"].add(pconfig["source_kbase_type"])
                    self.scripts_config["kbase_types"].add(pconfig["destination_kbase_type"])
                    id = "{0}=>{1}".format(pconfig["source_kbase_type"],pconfig["destination_kbase_type"])

                self.scripts_config[pconfig["script_type"]][k] = json.dumps(pconfig)
                del self.scripts_config[pconfig["script_type"]][k]["script_type"]
            except Exception, e:
                self.kbaseLogger.log_message("WARNING", "Unable to read plugin {0}: {1}".format(n,e.message))

        self.kbaseLogger.log_message("INFO", json.dumps(self.scripts_config["validate"], indent=4, sort_keys=True))        
        self.kbaseLogger.log_message("INFO", json.dumps(self.scripts_config["transform.upload"], indent=4, sort_keys=True))        
        self.kbaseLogger.log_message("INFO", json.dumps(self.scripts_config["transform.download"], indent=4, sort_keys=True))        
        self.kbaseLogger.log_message("INFO", json.dumps(self.scripts_config["convert"], indent=4, sort_keys=True))        

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
        #END convert

        # At some point might do deeper type checking...
        if not isinstance(result, list):
            raise ValueError('Method convert return value ' +
                             'result is not type list as required.')
        # return the results
        return [result]
