import sys
import os
import shutil
import subprocess
import base64
import simplejson

from biokbase.Transform import script_utils

def report_exception(logger=None, report_details=None, cleanup_details=None):
    logger.error(report_details["message"])
    logger.exception(report_details["exc"])

    if report_details["ujs_job_id"] is not None:
        report_details["ujs"].complete_job(report_details["ujs_job_id"], 
                                           report_details["token"], 
                                           report_details["message"], 
                                           None, 
                                           None) 
    
    if not cleanup_details["keep_working_directory"]:
        cleanup(cleanup_details["working_directory"])
        

def cleanup(logger=None, directory=None):
    try:
        shutil.rmtree(directory)
    except IOError, e:
        report_exception("{0}".format(directory), e, ujs)


def gen_recursive_filelist(d):
    for root, directories, files in os.walk(d):
        for file in files:
            yield os.path.join(root, file)


def run_task(logger, arguments, debug=False):
    if logger is None:
        logger = script_utils.stderrlogger(__file__)

    h = TaskRunner(logger)
    h.run(arguments, debug)


class TaskRunner(object):
    def __init__(self, logger=None):
        #logger_stdout = script_utils.getStdoutLogger()
        if logger is None:
            self.logger = script_utils.stderrlogger(__file__)
        else:
            self.logger = logger


    def _build_command_list(self, arguments=None, debug=False):
        if debug:
            command_name = os.path.splitext(arguments["script_name"])[0]
        else:
            command_name = arguments["script_name"]
        
        command_list = [command_name]
        del arguments["script_name"]
        #del arguments["optional_arguments"]

        for k in arguments:
            command_list.append("--{0}".format(k))
            command_list.append("{0}".format(arguments[k]))
        print command_list

        return command_list


    def run(self, arguments=None, debug=False):
        task = subprocess.Popen(self._build_command_list(arguments,debug), stderr=subprocess.PIPE)
        sub_stdout, sub_stderr = task.communicate()

        if sub_stdout is not None:
            print sub_stdout
        if sub_stderr is not None:
            print >> sys.stderr, sub_stderr

        if task.returncode != 0:
            raise Exception(sub_stderr)


def PluginManager(directory=None, logger=script_utils.stderrlogger(__file__)):
    manager = PlugIns(directory, logger)
    return manager


class PlugIns(object):

    def __init__(self, pluginsDir, logger=script_utils.stderrlogger(__file__)):
        self.scripts_config = {"external_types": list(),
                               "kbase_types": list(),
                               "validate": dict(),
                               "upload": dict(),
                               "download": dict(),
                               "convert": dict()}

        self.logger = logger

        #pluginsDir = self.config["plugins_directory"]
        plugins = os.listdir(pluginsDir)
        
        for p in plugins:
            try:
                f = open(os.path.join(pluginsDir, p), 'r')
                pconfig = simplejson.loads(f.read())
                f.close()

                id = None
                
                if pconfig["script_type"] == "validate":
                    if pconfig["external_type"] not in self.scripts_config["external_types"]:
                        self.scripts_config["external_types"].append(pconfig["external_type"])
                    
                    id = pconfig["external_type"]
                elif pconfig["script_type"] == "upload":
                    if pconfig["external_type"] not in self.scripts_config["external_types"]:
		        self.scripts_config["external_types"].append(pconfig["external_type"])
                    
                    if pconfig["kbase_type"] not in self.scripts_config["kbase_types"]:
                        self.scripts_config["kbase_types"].append(pconfig["kbase_type"])
                    
                    id = "{0}=>{1}".format(pconfig["external_type"],pconfig["kbase_type"])
                elif pconfig["script_type"] == "download":
                    if pconfig["external_type"] not in self.scripts_config["external_types"]:
                        self.scripts_config["external_types"].append(pconfig["external_type"])
                    
                    if pconfig["kbase_type"] not in self.scripts_config["kbase_types"]:
                        self.scripts_config["kbase_types"].append(pconfig["kbase_type"])
                    
                    id = "{0}=>{1}".format(pconfig["kbase_type"],pconfig["external_type"])
                elif pconfig["script_type"] == "convert":
                    if pconfig["source_kbase_type"] not in self.scripts_config["kbase_types"]:
                        self.scripts_config["kbase_types"].append(pconfig["source_kbase_type"])
                    
                    if pconfig["destination_kbase_type"] not in self.scripts_config["kbase_types"]:
                        self.scripts_config["kbase_types"].append(pconfig["destination_kbase_type"])
                    
                    id = "{0}=>{1}".format(pconfig["source_kbase_type"],pconfig["destination_kbase_type"])

                self.scripts_config[pconfig["script_type"]][id] = pconfig
            except Exception, e:
                self.logger.warning("Unable to read plugin {0}: {1}".format(p,e.message))


    def get_handler_args(self, method, args):

        if "optional_arguments" not in args:
            args["optional_arguments"] = '{}'

        job_details = dict()        

        self.logger.debug((method, args))

        if method == "upload":
            args["url_mapping"] = base64.urlsafe_b64encode(simplejson.dumps(args["url_mapping"]))

            if self.scripts_config["validate"].has_key(args["external_type"]):
                plugin_key = args["external_type"]

                self.logger.debug(self.scripts_config["validate"][plugin_key])
                        
                job_details["validate"] = self.scripts_config["validate"][plugin_key]
                #job_details["validate"] = dict()
                #job_details["validate"]["script_name"] = self.scripts_config["validate"][plugin_key]["script_name"]

                job_details["validate"] = self.scripts_config["validate"][plugin_key]
                
                self.logger.debug(job_details)
            else:
                self.logger.warning("No validation available for {0}".format(args["external_type"]))

            if self.scripts_config["upload"].has_key("{0}=>{1}".format(args["external_type"],args["kbase_type"])):
                plugin_key = "{0}=>{1}".format(args["external_type"],args["kbase_type"])
            
                job_details["transform"] = self.scripts_config["upload"][plugin_key]
                #job_details["transform"] = dict()
                #job_details["transform"]["script_name"] = self.scripts_config["upload"][plugin_key]["script_name"]

                for field in self.scripts_config["upload"][plugin_key]["handler_options"]["required_fields"]:
                    if field in args:
                        job_details["transform"][field] =  args[field]
                    else:
                        self.logger.error("Required field not present : {0}".format(field))
                
                for field in self.scripts_config["upload"][plugin_key]["handler_options"]["optional_fields"]:
                    if field in args:
                        job_details["transform"][field] =  args[field]
                    else:
                        self.logger.info("Optional field not present : {0}".format(field))
            else:
                raise Exception("No conversion available for {0} => {1}".format(args["external_type"],args["kbase_type"]))
                
            self.logger.info(simplejson.dumps(job_details, indent=4, sort_keys=True))
        elif method == "download":
            if self.scripts_config["download"].has_key("{0}=>{1}".format(args["kbase_type"],args["external_type"])):
                plugin_key = "{0}=>{1}".format(args["kbase_type"],args["external_type"])
            
                job_details["transform"] = self.scripts_config["download"][plugin_key]

                for field in self.scripts_config["download"][plugin_key]["handler_options"]["required_fields"]:
                    if field in args:
                        job_details["transform"][field] =  args[field]
                    else:
                        self.logger.error("Required field not present : {0}".format(field))
                
                for field in self.scripts_config["download"][plugin_key]["handler_options"]["optional_fields"]:
                    if field in args:
                        job_details["transform"][field] =  args[field]
                    else:
                        self.logger.info("Optional field not present : {0}".format(field))
            else:
                raise Exception("No conversion available for {0} => {1}".format(args["kbase_type"],args["external_type"]))
        elif method == "convert":
            if self.scripts_config["convert"].has_key("{0}=>{1}".format(args["source_kbase_type"],args["destination_kbase_type"])):
                plugin_key = "{0}=>{1}".format(args["source_kbase_type"],args["destination_kbase_type"])
            
                job_details["transform"] = self.scripts_config["convert"][plugin_key]

                for field in self.scripts_config["convert"][plugin_key]["handler_options"]["required_fields"]:
                    if field in args:
                        job_details["transform"][field] =  args[field]
                    else:
                        self.logger.error("Required field not present : {0}".format(field))
                
                for field in self.scripts_config["convert"][plugin_key]["handler_options"]["optional_fields"]:
                    if field in args:
                        job_details["transform"][field] =  args[field]
                    else:
                        self.logger.info("Optional field not present : {0}".format(field))

            else:
                raise Exception("No conversion available for {0} => {1}".format(args["source_kbase_type"],args["destination_kbase_type"]))
                
        args["job_details"] = base64.urlsafe_b64encode(simplejson.dumps(job_details))
        args["optional_arguments"] = base64.urlsafe_b64encode(simplejson.dumps(args["optional_arguments"]))
        return args

