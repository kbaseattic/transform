import sys
import os
import shutil
import subprocess

from biokbase.Transform import script_utils

def report_exception(logger=None, report_details=None, cleanup_details=None):
    logger.error(report_details["message"])
    logger.exception(report_details["exc"])

    if report_details["ujs_job_id"] is not None:
        report_details["ujs"].complete_job(report_details["ujs_job_id"], 
                                           report_details["token"], 
                                           report_details["message"], 
                                           {}, 
                                           {}) 
    
    if not cleanup_details["keep_working_directory"]:
        cleanup(cleanup_details["working_directory"])
    
    sys.exit(1);


def cleanup(logger=None, directory=None):
    try:
        shutil.rmtree(d)
    except IOError, e:
        report_exception("".format(directory), e, ujs)


def gen_recursive_filelist(d):
    for root, directories, files in os.walk(d):
        for file in files:
            yield os.path.join(root, file)


def run_task(logger, arguments):
    if logger is None:
        logger = script_utils.stderrlogger(__file__)

    h = TaskRunner(logger)
    h.run(arguments)


class TaskRunner(object):
    def __init__(self, logger=None):
        #logger_stdout = script_utils.getStdoutLogger()
        if logger is None:
            self.logger = script_utils.stderrlogger(__file__)
        else:
            self.logger = logger


    def _build_command_list(self, arguments=None):
        command_name = os.path.splitext(arguments["script_name"])[0]
        command_list = [command_name]

        for k in arguments:
            command_list.append("--{0}".format(k))
            command_list.append("{0}".format(arguments[k]))

        return command_list


    def run(self, arguments=None):
        task = subprocess.Popen(self._build_command_list(arguments), stderr=subprocess.PIPE)
        sub_stdout, sub_stderr = task.communicate()

        if sub_stdout is not None:
            print sub_stdout
        if sub_stderr is not None:
            print >> sys.stderr, sub_stderr

        if task.returncode != 0:
            raise Exception(sub_stderr)
