#BEGIN_HEADER
from biokbase.workflow.KBW import run_async
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
    #END_CLASS_HEADER

    # config contains contents of config file in a hash or None if it couldn't
    # be found
    def __init__(self, config):
        #BEGIN_CONSTRUCTOR
        self.config = config
        #END_CONSTRUCTOR
        pass

    def import_data(self, ctx, args):
        # ctx is the context object
        # return variables are: result
        #BEGIN import_data
        if 'optional_args' not in args: args['optional_args'] = '{}'
        result = run_async(self.config, ctx, args)
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
        if 'optional_args' not in args: args['optional_args'] = '{}'
        result = run_async(self.config, ctx, args)
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
        if 'optional_args' not in args: args['optional_args'] = '{}'
        result = run_async(self.config, ctx, args)
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
        if 'optional_args' not in args: args['optional_args'] = '{}'
        result = run_async(self.config, ctx, args)
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
        #END method_config

        # At some point might do deeper type checking...
        if not isinstance(result, dict):
            raise ValueError('Method method_config return value ' +
                             'result is not type dict as required.')
        # return the results
        return [result]
