'''
Created on Jan 30, 2015

@author: gaprice@lbl.gov
'''
import os
from biokbase.Transform import script_utils, drivers
from bzrlib.config import ConfigObj
import random
import sys
from biokbase.Transform.drivers import TransformTaskRunnerDriver


CLIENT_SHORTCUTS = {drivers.WS_CLIENT: 'ws',
                    drivers.HANDLE_CLIENT: 'handle',
                    drivers.UJS_CLIENT: 'ujs'}

URL_SHORTCUTS = {drivers.WS_URL: 'ws_url',
                 drivers.UJS_URL: 'ujs_url',
                 drivers.SHOCK_URL: 'shock_url'}

TEST_CFG_FILE = 'test.cfg'

FILE_LOC = os.path.split(__file__)[0]

sys.path.append(os.path.join(FILE_LOC, '../'))  # to import demo/setup
# this import is both resolved and used
from demo.setup import TransformVirtualEnv  # @UnresolvedImport @UnusedImport

TRANSFORM_LOC = os.path.join(FILE_LOC, '../../')
# maybe this should be configurable...?
PLUGIN_CFG_LOC = os.path.join(TRANSFORM_LOC, 'plugins/configs')
TEST_CFG_LOC = os.path.join(FILE_LOC, TEST_CFG_FILE)


class Test_Scripts(object):

    _keep_venv = False

    @classmethod
    def setup_class(cls):
        '''
        Sets up the token, service urls, and service clients for use in
        tests.
        '''
        cls.token = script_utils.get_token()

        cfg = ConfigObj(TEST_CFG_LOC)
        for url in URL_SHORTCUTS:
            setattr(cls, URL_SHORTCUTS[url], cfg.get(url))

        cls.runner = TransformTaskRunnerDriver(cfg, PLUGIN_CFG_LOC)
        for cli in CLIENT_SHORTCUTS:
            setattr(cls, CLIENT_SHORTCUTS[cli], getattr(cls.runner, cli))

        tve = TransformVirtualEnv(FILE_LOC, 'venv', TRANSFORM_LOC,
                                  keep_current_venv=cls._keep_venv)
        tve.activate_for_current_py_process()

        cls.staged = {}
        cls.stage_data()

    @classmethod
    def keep_current_venv(cls, keep=True):
        '''
        Call *prior* to calling setup_class() to keep the previously built
        virtual environment.
        '''
        cls._keep_venv = keep

    @classmethod
    def stage_data(cls):
        '''Override to stage data for all tests'''
        pass

    @classmethod
    def upload_file_to_shock_and_get_handle(cls, test_file):
        '''
        Uploads the file in test_file to shock and returns the node and a
        handle to the node.
        '''
        node_id = script_utils.upload_file_to_shock(
            shock_service_url=cls.shock_url,
            filePath=test_file,
            ssl_verify=False,
            token=cls.token)['id']

        handle_id = cls.handle.persist_handle({'id': node_id,
                                               'type': 'shock',
                                               'url': cls.shock_url
                                               })
        return node_id, handle_id

    @classmethod
    def create_random_workspace(cls, prefix):
        '''
        Creates a workspace with a name consisting of prefix appended
        with a random number and returns the new name.
        '''
        ws_name = prefix + '_' + str(random.random())[2:]
        wsinfo = cls.ws.create_workspace({'workspace': ws_name})
        return wsinfo[1]

    @classmethod
    def run_taskrunner(cls, method, args):
        '''
        Runs a task runner of type method with arguments args.
        Method is one of 'convert', 'upload', or 'download'.
        Returns a tuple with the standard output as a string, the standard
        error as a string, and the script return code.
        '''
        _, results = cls.runner.run_job(method, args)
        return results['stdout'], results['stderr'], results['exit_code']

    @classmethod
    def run_and_check(cls, method, args, expect_out, expect_err,
                      not_expect_out=None, not_expect_err=None,
                      ret_code=0):
        '''
        Runs a task runner of type method with arguments args.
        Method is one of 'convert', 'upload', or 'download'.
        If expect_out or expect_err is None, the respective io stream is
        expected to be empty; otherwise a test error will result.
        If they are not None, the string provided must be in the respective
        io stream.
        If not_expect_out or not_expect_err is provided, the string must not
        be in the respective io stream.
        ret_code specifies the expected return code of the script, defaulting
        to 0.
        '''
        stdo, stde, code = cls.run_taskrunner(method, args)
        if not expect_out and stdo:
            raise TestException('Got unexpected data in standard out:\n' +
                                stdo)
        if stdo and expect_out not in stdo:
            raise TestException('Did not get expected data in stdout:\n' +
                                stdo)
        if stdo and not_expect_out and not_expect_out in stdo:
            raise TestException('Got unexpected data in standard out:\n' +
                                stdo)

        if not expect_err and stde:
            raise TestException('Got unexpected data in standard err:\n' +
                                stde)
        if stde and expect_err not in stde:
            raise TestException('Did not get expected data in stderr:\n' +
                                stde)
        if stde and not_expect_err and not_expect_err in stde:
            raise TestException('Got unexpected data in standard out:\n' +
                                stdo)

        if ret_code != code:
            raise TestException('Got unexpected return code from script:' +
                                str(code))


class TestException(Exception):
    pass
