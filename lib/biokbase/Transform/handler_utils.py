"""
Provides utility functions for handler/taskrunner level code to provide consistent
behavior across different taskrunners and reduce code repetition of similar tasks.
"""

import sys
import os
import time
import datetime
import shutil
import subprocess
import base64
import simplejson
import pty
import select
import functools
import threading
import signal
import Queue

from biokbase.Transform import script_utils

UJS_STATUS_MAX = 200

def report_exception(logger=None, report_details=None, cleanup_details=None):
    """
    Report a fatal error from a taskrunner script back to UJS if possible.
    Clean up the working directory that the job was running in before exiting.
    """

    if logger is None:
        raise Exception("A logger must be defined!")

    logger.debug(report_details)
    logger.error(report_details["error_message"])

    if report_details["ujs_job_id"] is not None:
        ujs = report_details["ujs_client"]
        
        job_status = ujs.get_job_status(report_details["ujs_job_id"])

        if job_status[-2] == 0:
            ujs.complete_job(report_details["ujs_job_id"], 
                             report_details["token"], 
                             report_details["status"][:UJS_STATUS_MAX], 
                             report_details["error_message"], 
                             None)
    else:
        raise Exception("No report details included!") 
    
    if cleanup_details is not None:    
        if not cleanup_details["keep_working_directory"]:
            try:
                cleanup(logger=logger, directory=cleanup_details["working_directory"])            
            except Exception, e:
                logger.exception(e)
    else:
        raise Exception("Unable to cleanup working directory without cleanup info!")
        

def cleanup(logger=None, directory=None):
    """
    Clean up after the job.  At the moment this just means removing the working
    directory, but later could mean other things.
    """
    
    try:
        shutil.rmtree(directory)
    except IOError, e:
        logger.error("Unable to remove working directory {0}".format(directory))
        raise


def gen_recursive_filelist(d):
    """
    Generate a list of all files present below a given directory.
    """
    
    for root, directories, files in os.walk(d):
        for file in files:
            yield os.path.join(root, file)


def run_task(logger, arguments, debug=False, callback=None):
    """
    A factory function to abstract the implementation details of how tasks are run.
    """

    if logger is None:
        logger = script_utils.stderrlogger(__file__)

    h = TaskRunner(logger, callback=callback)
    out = h.run(arguments, debug)
    return out


class TaskRunner(object):
    """
    A simple task runner that builds a command line call from a given config, runs
    the command and reports back the stdout and stderr of the task if it succeeds,
    or raises an exception if the task fails, which is detected at the moment by the
    return code of the task.
    """
    
    def __init__(self, logger=None, callback=None):
        #logger_stdout = script_utils.getStdoutLogger()
        if logger is None:
            self.logger = script_utils.stderrlogger(__file__)
        else:
            self.logger = logger
            
        if callback is None:
            self.callback = lambda x: self.logger.info(x)
        else:
            self.callback = callback


    def _build_command_list(self, arguments=None, debug=False):
        """
        Generate the command argument list.  If debug is True you are running in a mode
        where the scripts are expected to be run directly.  In a KBase environment,
        each script is wrapped in a bash shell script that sets some environment
        variables, so we strip out the actual script extension to make sure that the
        correct entity is invoked when the job runs.
        """
        
        if debug:
            command_name = arguments["script_name"]
        else:
            command_name = os.path.splitext(arguments["script_name"])[0]
        
        command_list = [command_name]
        #del arguments["script_name"]
        #del arguments["optional_arguments"]

        for k in arguments:
            if k == "script_name": continue
            if type(arguments[k]) == type(list()):
                for n in arguments[k]:
                    command_list.append("--{0}".format(k))
                    command_list.append("{0}".format(n))
            else:            
                command_list.append("--{0}".format(k))
                command_list.append("{0}".format(arguments[k]))
        
        return command_list


    def run(self, arguments=None, debug=False):
        """
        Executes the task while monitoring stdout and stderr for messages.

        For each line of stdout, run a callback function that does "something".
        The default behavior for the callback would be to log the message, but other behavior can be swapped in,
        for instance to communicate back to a UJS process what the job status is.

        If the child process exits with an error, collect the stdout and stderr output and report in an exception.
        """

        # kill the child process if we receive a terminate signal
        def terminate_child_process(child, signum, frame):
            try:
                if child and signum != signal.SIGINT:
                    child.terminate()
                    child.wait()
            finally:
                sys.exit()

        # poll the pty for available data to read, then push to a queue and signal ready
        def produce_queue(queue, master_fd, slave_fd, evt, process_completed):
            with os.fdopen(master_fd, 'rb', 0) as task_stream:
                while 1:
                    ready = select.select([master_fd], [], [], 0)[0]

                    # exit if our process has terminated and no more input
                    if not ready and process_completed.isSet():
                        os.close(slave_fd)
                        evt.set()
                        break

                    if master_fd in ready:
                        # POSIX.1 requires PIPE_BUF to be at least 512 bytes, but Linux uses 4096 bytes
                        data = os.read(master_fd, 4096)

                        if not data:
                            # reached EOF, signal data ready in case the queue is not empty, then exit
                            evt.set()
                            break
                        else:
                            # put data in the queue and signal the consumer thread
                            queue.put(data)
                            evt.set()

        # wait for ready signal, then read data from queue and save to a buffer
        # once the buffer contains an end of line, send that to a callback if defined,
        # then send the line to a file for later processing
        def consume_queue(queue, filename, evt, process_completed, callback=None):
            streambuffer = []
            with open(filename, 'w+') as fileobj:
                while 1:
                    # wait for a signal at most one second at a time so we can check the child process status
                    evt.wait(1)
                    if queue.empty() and process_completed.isSet():
                        # make sure the last part of the buffer is written out
                        if streambuffer:
                            if callback:
                                callback(streambuffer[0])

                            fileobj.write(streambuffer[0])
                            fileobj.flush()
                        break
                    elif queue.empty():
                        # the queue is empty, but our child process has not exited yet, so data may show up still
                        continue

                    data = queue.get_nowait()
                    streambuffer.append(data)
                    queue.task_done()

                    # As soon as we see an end of line from the stream, we should write.
                    # Since we could receive many lines per queue chunk, we want to pass
                    # a line at a time to our callback.
                    if '\n' in data:
                        merged = "".join(streambuffer)
                        lines = merged.split('\n')

                        if len(lines) > 1 and '\n' not in lines[-1]:
                            streambuffer = [lines[-1]]
                            lines.pop()
                        else:
                            streambuffer = []

                        if callback:
                            for x in lines:
                                if not x:
                                    continue
                                callback(x)

                        fileobj.write("".join(lines))
                        fileobj.flush()

        command_list = self._build_command_list(arguments,debug)

        self.logger.info("Executing {0}".format(" ".join(command_list)))

        stdout_name = 'task_stdout_{}'.format(datetime.datetime.utcnow().isoformat())
        stderr_name = 'task_stderr_{}'.format(datetime.datetime.utcnow().isoformat())

        stderr = open(stderr_name, 'w+')

        # Use pty to provide a workaround for buffer overflow in stdio when monitoring stdout
        master_stdout_fd, slave_stdout_fd = pty.openpty()
        #master_stderr_fd, slave_stderr_fd = pty.openpty()
        #task = subprocess.Popen(command_list, stdout=slave_stdout_fd, stderr=slave_stderr_fd, close_fds=True)
        task = subprocess.Popen(command_list, stdout=slave_stdout_fd, stderr=stderr.fileno(), close_fds=True)

        # force termination signal handling of the child process
        signal_handler = functools.partial(cleanup, task)
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        stdout_queue = Queue.Queue()
        stdout_data_ready = threading.Event()
        process_completed = threading.Event()

        t1 = threading.Thread(target=produce_queue, args=(stdout_queue, master_stdout_fd, slave_stdout_fd, stdout_data_ready, process_completed))
        t1.daemon = True
        t1.start()

        t2 = threading.Thread(target=consume_queue, args=(stdout_queue, stdout_name, stdout_data_ready, process_completed, self.callback))
        t2.daemon = True
        t2.start()

        #stderr_queue = Queue.Queue()
        #stderr_data_ready = threading.Event()

        #t3 = threading.Thread(target=produce_queue, args=(stderr_queue, master_stderr_fd, slave_stderr_fd, stderr_data_ready, task))
        #t3.daemon = True
        #t3.start()

        #t4 = threading.Thread(target=consume_queue, args=(stderr_queue, stderr_name, stderr_data_ready, task))
        #t4.daemon = True
        #t4.start()

        task.wait()
        process_completed.set()

        t1.join()
        t2.join()
        #t3.join()
        #t4.join()

        stdout = open(stdout_name, 'rb')
        #stderr = open(stderr_name, 'rb')
        stderr.seek(0)

        task_output = {}
        task_output["stdout"] = "".join(stdout.readlines())
        task_output["stderr"] = "".join(stderr.readlines())

        stdout.close()
        stderr.close()
        os.remove(stdout_name)
        os.remove(stderr_name)

        if task.returncode != 0:
            self.logger.error(task.returncode)
            raise Exception(task_output["stdout"], task_output["stderr"])
        else:
            return task_output


def PluginManager(directory=None, logger=script_utils.stderrlogger(__file__)):
    if directory is None:
        raise Exception("Must provide a directory to read plugin configs from!")

    manager = PlugIns(directory, logger)
    return manager


class PlugIns(object):

    # read in all configs
    def __init__(self, plugins_directory=None, logger=script_utils.stderrlogger(__file__)):
        self.scripts_config = {"external_types": list(),
                               "kbase_types": list(),
                               "validate": dict(),
                               "upload": dict(),
                               "download": dict(),
                               "convert": dict()}

        self.logger = logger

        plugins = sorted(os.listdir(plugins_directory))
        
        for p in plugins:
            try:
                f = open(os.path.join(plugins_directory, p), 'r')
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

                self.logger.info("Successfully added plugin {0}".format(p))
            except Exception, e:
                self.logger.warning("Unable to read plugin {0}: {1}".format(p,e.message))


    def get_job_details(self, method, args):
        job_details = dict()        

        if method == "upload":
            if self.scripts_config["validate"].has_key(args["external_type"]):
                plugin_key = args["external_type"]
                
                job_details["validate"] = self.scripts_config["validate"][plugin_key]
            else:
                self.logger.warning("No validation available for {0}".format(args["external_type"]))

            if self.scripts_config["upload"].has_key("{0}=>{1}".format(args["external_type"],args["kbase_type"])):
                plugin_key = "{0}=>{1}".format(args["external_type"],args["kbase_type"])
            
                job_details["transform"] = self.scripts_config["upload"][plugin_key]
            else:
                raise Exception("No conversion available for {0} => {1}".format(args["external_type"],args["kbase_type"]))
        elif method == "download":
            if self.scripts_config["download"].has_key("{0}=>{1}".format(args["kbase_type"],args["external_type"])):
                plugin_key = "{0}=>{1}".format(args["kbase_type"],args["external_type"])
            
                job_details["transform"] = self.scripts_config["download"][plugin_key]
            else:
                raise Exception("No conversion available for {0} => {1}".format(args["kbase_type"],args["external_type"]))
        elif method == "convert":
            if self.scripts_config["convert"].has_key("{0}=>{1}".format(args["source_kbase_type"],args["destination_kbase_type"])):
                plugin_key = "{0}=>{1}".format(args["source_kbase_type"],args["destination_kbase_type"])
            
                job_details["transform"] = self.scripts_config["convert"][plugin_key]
            else:
                raise Exception("No conversion available for {0} => {1}".format(args["source_kbase_type"],args["destination_kbase_type"]))
        else:
            raise Exception("Unknown method {0}".format(method))
        
        return job_details

