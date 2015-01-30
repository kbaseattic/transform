'''
Created on Jan 30, 2015

@author: gaprice@lbl.gov
'''
from __future__ import print_function
import os
import inspect
from biokbase.Transform import script_utils
from biokbase.Transform.handler_utils import PlugIns
from biokbase.AbstractHandle.Client import AbstractHandle
from bzrlib.config import ConfigObj
import json
from biokbase.workspace.client import Workspace
import random
import sys
import subprocess


KB_TOKEN = 'KB_AUTH_TOKEN'
TEST_CFG_FILE = 'test.cfg'

FILE_LOC = os.path.split(__file__)[0]

sys.path.append(os.path.join(FILE_LOC, '../'))  # to import demo/setup
# this import is both resolved and used
from demo.setup import TransformVirtualEnv  # @UnresolvedImport @UnusedImport

TRANSFORM_LOC = os.path.join(FILE_LOC, '../../')
# maybe this should be configurable...?
PLUGIN_CFG_LOC = os.path.join(TRANSFORM_LOC, 'plugins/configs')


class Test_Scripts(object):

    @classmethod
    def setup_class(cls):
        cls.token = os.environ.get(KB_TOKEN)
        if not cls.token:
            raise ValueError('No token found in environment variable ' +
                             KB_TOKEN)
        cls.plugins_cfg = PlugIns(PLUGIN_CFG_LOC)
        cfg = ConfigObj(TEST_CFG_FILE)
        for url in ['ws_url', 'shock_url', 'handle_url', 'ujs_url']:
            setattr(cls, url, cfg.get(url))
        tve = TransformVirtualEnv(FILE_LOC, 'venv', TRANSFORM_LOC,
                                  keep_current_venv=False)
        tve.activate_for_current_py_process()

    def upload_file_to_shock_and_get_handle(self, test_file):
        node_id = script_utils.upload_file_to_shock(
            shock_service_url=self.shock_url,
            filePath=test_file,
            ssl_verify=False,
            token=self.token)['id']

        handle = AbstractHandle(self.handle_url, token=self.token)
        handle_id = handle.persist_handle({'id': node_id,
                                           'type': 'shock',
                                           'url': self.shock_url
                                           })
        return node_id, handle_id

    def create_random_workspace(self, prefix):
        ws = Workspace(self.ws_url, token=self.token)
        ws_name = prefix + '_' + str(random.random())[2:]
        wsinfo = ws.create_workspace({'workspace': ws_name})
        return wsinfo[1]

    def run_convert_taskrunner(self, args):
        input_args = self.plugins_cfg.get_handler_args("convert", args)
        command_list = ['trns_convert_taskrunner.py']

        for k in input_args:
            command_list.append("--{0}".format(k))
            command_list.append("{0}".format(input_args[k]))

        task = subprocess.Popen(command_list, stderr=subprocess.PIPE)
        return task.communicate()

    def test_assyfile_to_cs_basic_ops(self):
        this_function_name = sys._getframe().f_code.co_name
        src_obj_name = 'foo'
        dest_obj_name = 'foo2'
        src_type = 'KBaseFile.AssemblyFile'
        dest_type = 'KBaseGenomes.ContigSet'

        test_file = os.path.join(FILE_LOC, 'test_files/sample.fa')
        node_id, handle = self.upload_file_to_shock_and_get_handle(test_file)

        test_json = os.path.join(FILE_LOC, 'test_files/AssemblyFile.json')
        with open(test_json) as assyjsonfile:
            assyjson = json.loads(assyjsonfile.read())
        assyjson['assembly_file']['file']['url'] = self.shock_url
        assyjson['assembly_file']['file']['id'] = node_id
        assyjson['assembly_file']['file']['hid'] = handle

        ws_name1 = self.create_random_workspace(this_function_name)
        ws_name2 = self.create_random_workspace(this_function_name)
        ws = Workspace(self.ws_url, token=self.token)
        objdata = ws.save_objects(
            {'workspace': ws_name1,
             'objects': [{'name': src_obj_name,
                          'type': src_type,
                          'data': assyjson}]
             })[0]
        ref = str(objdata[6]) + '/' + str(objdata[1])

        args = {'source_kbase_type': src_type,
                'destination_kbase_type': dest_type,
                'source_workspace_name': ws_name1,
                'destination_workspace_name': ws_name2,
                'source_object_name': src_obj_name,
                'destination_object_name': dest_obj_name,
                'workspace_service_url': self.ws_url,
                'ujs_service_url': self.ujs_url,
                'working_directory': ws_name1}

        stdo, stde = self.run_convert_taskrunner(args)
        print(stdo)
        print("***")
        print(stde)


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
