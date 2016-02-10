#!/usr/bin/env python
'''
This is a template/example file for the transform test framework. You can see
an example of filled out frameworks in the other test directories in this
directory's parent.

To make a new set of tests, create a new directory in this directory's parent.
The directory *must* start with test_ for the tests to be automatically
discovered and run. Copy this file into the directory and rename it as
appropriate, but again the file name must start with test_.

More detailed instructions are in the code body below.

Created on Feb 4, 2015

@author: gaprice@lbl.gov
'''
from __future__ import print_function
import os
import sys

'''
Set this to true to skip rebuilding the test virtual environment. This only
has an effect when running this file directly.
'''
KEEP_CURRENT_VENV = False

'''
This code imports the superclass the tests inherit from. Don't change it.
'''
FILE_LOC = os.path.split(__file__)[0]
sys.path.append(os.path.join(FILE_LOC, '../'))
import script_checking_framework
from script_checking_framework import ScriptCheckFramework, TestException


class TestExample(ScriptCheckFramework):
    '''
    You can name this class anything you want as long as it starts with Test.
    This class comes with a number of useful things already set up. All of
    these helpers can be accessed in class methods via cls or instance methods
    via self.

    urls are set up as below:
    ws_url - workspace url
    ujs_url - user and job state url
    shock_url - shock url

    clients:
    ws - workspace client
    handle - handle service client
    ujs - user and job state client

    helper functions:
    node_id, handle_id = upload_file_to_shock_and_get_handle(test_file)
        uploads test file to shock and returs the shock node id and a handle id

    ws_name = create_random_workspace(prefix)
        creates a workspace with a name starting with prefix. The remainder of
        the name is a random number. Returns the workspace name.

    run_and_check(method, args, expect_out, expect_err,
                  not_expect_out=None, not_expect_err=None,
                  ret_code=0):
        Runs a task runner of type method with arguments args and checks the
            output.
        method is one of 'convert', 'upload', or 'download'.
        args is a dictionary mapping the command line parameter names of
            the taskrunner in question to their values.
        If expect_out or expect_err is None, the respective io stream is
            expected to be empty; otherwise a test error will result.
        If they are not None, the string provided must be in the respective
            io stream.
        If not_expect_out or not_expect_err is provided, the string must not
            be in the respective io stream.
        ret_code specifies the expected return code of the script, defaulting
            to 0.
    '''

    @classmethod
    def stage_data(cls):
        '''
        This method is called once per test run. You can use this method
        to stage data that can be used in multiple tests.
        Of course, you can always stage data in the test method itself.
        '''
        print('shock url in the stage_data method: ' + cls.shock_url)

    def test_example(self):
        '''
        Put test code in test methods like this. Any method starting with
        'test_' will be run when running this file directly or via the
        Makefile.
        Generally, the test will need to
        - stage data (see the stage_data) class method & the helper functions
            mentioned above
        - run the taskrunner (see the run_and_check helper method)
        - check the output either locally or in the workspace/shock
        As the tests develop we can add more helper methods for loading,
        retrieving, and checking data.
        '''
        print('the workspace url is ' + self.ws_url)
        with open(os.path.join(FILE_LOC, 'test_files/some_data')) as f:
            data = f.read()
        assert data == 'data'
        # or you can do
        if (data != 'data'):
            raise TestException('unexpected data')

# don't make any changes beyond this point


def main():
    # generally use nosetests to run these tests, this gets them to run
    # while testing the tests
    script_checking_framework.run_methods(__name__, KEEP_CURRENT_VENV)

if __name__ == '__main__':
    main()
