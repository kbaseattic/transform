'''
Created on Jan 30, 2015

@author: gaprice@lbl.gov
'''
from __future__ import print_function
import os
import inspect
from biokbase.Transform import script_utils, drivers
from bzrlib.config import ConfigObj
import json
import random
import sys
from deep_eq import deep_eq
from biokbase.Transform.drivers import TransformTaskRunnerDriver
from __builtin__ import classmethod


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
        cls._keep_venv = keep

    @classmethod
    def stage_data(cls):
        cls.stage_assy_files()
        cls.stage_empty_data()

    @classmethod
    def stage_empty_data(cls):
        this_function_name = sys._getframe().f_code.co_name
        src_obj_name = 'empty'
        src_type = 'Empty.AType'

        src_ws = cls.create_random_workspace(this_function_name)
        objdata = cls.ws.save_objects(
            {'workspace': src_ws,
             'objects': [{'name': src_obj_name,
                          'type': src_type,
                          'data': {}}]
             })[0]
        cls.staged['empty'] = {'obj_info': objdata}

    @classmethod
    def stage_assy_files(cls):
        this_function_name = sys._getframe().f_code.co_name
        src_ws = cls.create_random_workspace(this_function_name)
        cls.load_assy_file_data(
            'test_files/sample.fa', 'test_files/AssemblyFile.json', src_ws,
            'test_assy_file', 'assy_file')
        cls.load_assy_file_data(
            'test_files/sample.fa', 'test_files/AssemblyFile.json', src_ws,
            'test_assy_file_bad_node', 'assy_file_bad_node',
            with_bad_node_id=True)
        cls.load_assy_file_data(
            'test_files/sample_missing_data.fa',
            'test_files/AssemblyFile.json', src_ws,
            'test_assy_file_missing_data', 'assy_file_missing_data')
        cls.load_assy_file_data(
            'test_files/sample_missing_data_last.fa',
            'test_files/AssemblyFile.json', src_ws,
            'test_assy_file_missing_data_last', 'assy_file_missing_data_last')
        cls.load_assy_file_data(
            'test_files/sample_missing_data_ws.fa',
            'test_files/AssemblyFile.json', src_ws,
            'test_assy_file_missing_data_ws', 'assy_file_missing_data_ws')
        cls.load_assy_file_data(
            'test_files/empty.fa',
            'test_files/AssemblyFile.json', src_ws,
            'test_assy_file_empty', 'assy_file_empty')

    @classmethod
    def load_assy_file_data(cls, fa_file, ws_file, src_ws, src_obj_name, key,
                            with_bad_node_id=False):
        src_type = 'KBaseFile.AssemblyFile'
        test_file = os.path.join(FILE_LOC, fa_file)
        node_id, handle = cls.upload_file_to_shock_and_get_handle(test_file)
        if (with_bad_node_id):
            node_id += '1'

        test_json = os.path.join(FILE_LOC, ws_file)
        with open(test_json) as assyjsonfile:
            assyjson = json.loads(assyjsonfile.read())
        assyjson['assembly_file']['file']['url'] = cls.shock_url
        assyjson['assembly_file']['file']['id'] = node_id
        assyjson['assembly_file']['file']['hid'] = handle

        objdata = cls.ws.save_objects(
            {'workspace': src_ws,
             'objects': [{'name': src_obj_name,
                          'type': src_type,
                          'data': assyjson}]
             })[0]
        ref = str(objdata[6]) + '/' + str(objdata[0]) + '/' + str(objdata[4])
        cls.staged[key] = {'obj_info': objdata,
                           'node': node_id,
                           'ref': ref}

    @classmethod
    def upload_file_to_shock_and_get_handle(cls, test_file):
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
        ws_name = prefix + '_' + str(random.random())[2:]
        wsinfo = cls.ws.create_workspace({'workspace': ws_name})
        return wsinfo[1]

    @classmethod
    def run_taskrunner(cls, method, args):
        _, results = cls.runner.run_job(method, args)
        return results['stdout'], results['stderr'], results['exit_code']

    def test_assyfile_to_cs_basic_ops(self):
        this_function_name = sys._getframe().f_code.co_name
        staged = self.staged['assy_file']

        dest_ws = self.create_random_workspace(this_function_name)
        dest_obj_name = 'foo2'

        args = {'source_kbase_type': staged['obj_info'][2].split('-')[0],
                'destination_kbase_type': 'KBaseGenomes.ContigSet',
                'source_workspace_name': staged['obj_info'][7],
                'destination_workspace_name': dest_ws,
                'source_object_name': staged['obj_info'][1],
                'destination_object_name': dest_obj_name,
                'workspace_service_url': self.ws_url,
                'ujs_service_url': self.ujs_url,
                'working_directory': dest_ws}

        expect_err = 'INFO - Conversion completed.'
        self.run_and_check('convert', args, None, expect_err,
                           not_expect_err='ERROR')

        newobj = self.ws.get_objects([{'workspace': dest_ws,
                                       'name': dest_obj_name}])[0]
        prov = newobj['provenance'][0]
        ref = staged['ref']
        assert prov['input_ws_objects'] == [ref]
        assert prov['resolved_ws_objects'] == [ref]
        assert prov['script'] ==\
            'trns_transform_KBaseFile_AssemblyFile_to_KBaseGenomes_ContigSet'
        assert prov['script_ver'] == '0.0.1'

        with open(os.path.join(FILE_LOC, 'test_files/ContigSetOut.json')) as f:
            expected = json.loads(f.read())
        expected['fasta_ref'] = staged['node']
        deep_eq(expected, newobj['data'], _assert=True)

    def test_assyfile_to_cs_fail_ws_error(self):
        this_function_name = sys._getframe().f_code.co_name
        staged = self.staged['assy_file']

        src_ws = staged['obj_info'][7]

        args = {'source_kbase_type': staged['obj_info'][2].split('-')[0],
                'destination_kbase_type': 'KBaseGenomes.ContigSet',
                'source_workspace_name': src_ws + 'thisllbreakthings',
                'destination_workspace_name': 'no-such-ws%$^%',
                'source_object_name': staged['obj_info'][1],
                'destination_object_name': 'foo2',
                'workspace_service_url': self.ws_url,
                'ujs_service_url': self.ujs_url,
                'working_directory': this_function_name}

        expect = 'Object test_assy_file cannot be accessed: No workspace ' +\
            'with name stage_assy_file'
        self.fail_convert(args, expect)

    def test_assyfile_to_cs_fail_ws_type(self):
        this_function_name = sys._getframe().f_code.co_name
        expect = 'This method only works on the KBaseFile.AssemblyFile type'
        self.fail_on_assyfile_staged_data('empty', expect, this_function_name)

    def test_assyfile_to_cs_fail_missing_data(self):
        this_function_name = sys._getframe().f_code.co_name
        expect = 'There is no sequence related to FASTA record: id2 desc2'
        self.fail_on_assyfile_staged_data(
            'assy_file_missing_data', expect, this_function_name)

    def test_assyfile_to_cs_fail_missing_data_last(self):
        this_function_name = sys._getframe().f_code.co_name
        expect = 'There is no sequence related to FASTA record: id4 desc4'
        self.fail_on_assyfile_staged_data(
            'assy_file_missing_data_last', expect, this_function_name)

    def test_assyfile_to_cs_fail_missing_data_whitespace(self):
        this_function_name = sys._getframe().f_code.co_name
        expect = 'There is no sequence related to FASTA record: id3 desc3'
        self.fail_on_assyfile_staged_data(
            'assy_file_missing_data_ws', expect, this_function_name)

    def test_assyfile_to_cs_fail_empty_file(self):
        this_function_name = sys._getframe().f_code.co_name
        expect = 'There are no contigs in this file'
        self.fail_on_assyfile_staged_data(
            'assy_file_empty', expect, this_function_name)

    def test_assyfile_to_cs_fail_bad_shock_node(self):
        this_function_name = sys._getframe().f_code.co_name
        expect = 'Node not found'
        self.fail_on_assyfile_staged_data(
            'assy_file_bad_node', expect, this_function_name)

    def fail_on_assyfile_staged_data(self, key, error, working_dir):
        staged = self.staged[key]

        args = {'source_kbase_type': 'KBaseFile.AssemblyFile',
                'destination_kbase_type': 'KBaseGenomes.ContigSet',
                'source_workspace_name': staged['obj_info'][7],
                'destination_workspace_name': 'no-such-ws%$^%',
                'source_object_name': staged['obj_info'][1],
                'destination_object_name': 'foo2',
                'workspace_service_url': self.ws_url,
                'ujs_service_url': self.ujs_url,
                'working_directory': working_dir}

        self.fail_convert(args, error)

    def fail_convert(self, args, expected_error):
        self.run_and_check('convert', args, None, expected_error, ret_code=1)

    @classmethod
    def run_and_check(cls, method, args, expect_out, expect_err,
                      not_expect_out=None, not_expect_err=None,
                      ret_code=0):
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


def main():
    # use nosetests to run these tests, this is a hack to get them to run
    # while testing the tests
    Test_Scripts.setup_class()
    ts = Test_Scripts()
    methods = inspect.getmembers(ts, predicate=inspect.ismethod)
    for meth in methods:
        if meth[0].startswith('test_'):
            print("\nRunning " + meth[0])
            meth[1]()


if __name__ == '__main__':
    main()
