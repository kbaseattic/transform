#BEGIN_HEADER
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
        #END_CONSTRUCTOR
        pass

    def import_data(self, ctx, args):
        # ctx is the context object
        # return variables are: result
        #BEGIN import_data
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
        #END download

        # At some point might do deeper type checking...
        if not isinstance(result, list):
            raise ValueError('Method download return value ' +
                             'result is not type list as required.')
        # return the results
        return [result]
