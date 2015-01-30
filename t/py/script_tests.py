'''
Created on Jan 30, 2015

@author: gaprice@lbl.gov
'''
from __future__ import print_function
import os
import inspect
from biokbase.Transform.handler_utils import PlugIns
from bzrlib.config import ConfigObj

KB_TOKEN = 'KB_AUTH_TOKEN'
TEST_CFG_FILE = 'test.cfg'

# maybe this should be configurable...?
PLUGIN_CFG_LOC = os.path.join(os.path.split(__file__)[0],
                              '../../plugins/configs')


class Test_Scripts(object):

    @classmethod
    def setup_class(cls):
        cls.token = os.environ.get(KB_TOKEN)
        if not cls.token:
            raise ValueError('No token found in environment variable ' +
                             KB_TOKEN)
        cls.plugins_cfg = PlugIns(PLUGIN_CFG_LOC)
        cls.set_configs()

    @classmethod
    def set_configs(cls):
        cfg = ConfigObj(TEST_CFG_FILE)
        for url in ['ws_url', 'shock_url', 'handle_url', 'ujs_url']:
            setattr(cls, url, cfg.get(url))

    def test_fake(self):
        print(self.ws_url)


def main():
    # use nosetests to run these tests, this is a hack to get them to run
    # while testing the tests
    Test_Scripts.setup_class()
    ts = Test_Scripts()
    methods = inspect.getmembers(ts, predicate=inspect.ismethod)
    for meth in methods:
        if meth[0].startswith('test_'):
            meth[1]()


if __name__ == '__main__':
    main()
