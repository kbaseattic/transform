#!/usr/bin/env python

# standard library imports
import sys
import os
import argparse
import logging

# 3rd party imports
import simplejson

# KBase imports
import biokbase.Transform.script_utils as script_utils


# all your work takes place in here
def transform(shock_service_url=None, handle_service_url=None, 
              working_directory=None, level=logging.INFO, logger=None)
    """
    Template transform script for python.
    
    Args:
        shock_service_url: If you have shock references you need to make.
        handle_service_url: In case your type has at least one handle reference.
        working_directory: A directory where you can do work.
    
    Returns:
        JSON representing a KBase object.
    
    Authors:
        Your name here
    
    """

    # there are utility functions for things you need to do, like log messages
    if logger is None:
        logger = script_utils.stderrlogger(__file__)
    
    logger.info("Python KBase Upload template transform script")
    
    # here is how you get the user token to access services
    token = os.environ.get("KB_AUTH_TOKEN")
    
    # stuff happens in here, transform the data
    
    # now make your JSON object
    objectString = json.dumps("{}", sort_keys=True, indent=4)
    
    # write it to disk
    
    logger.info("Transform completed.")
    

# we don't do anything special in here, just basically wrap the function above
if __name__ == "__main__":
    # We're going to parse our docstring above and use that for help text, 
    # so your argument names need to match what is in the docstring or your script
    # will throw an exception.
    script_details.parse_docs(transform.__doc__)

    parser = argparse.ArgumentParser(prog=__file__, 
                                     description=script_details["Description"],
                                     epilog=script_details["Authors"])
    parser.add_argument("--shock_service_url", 
                        help=script_details["Args"]["shock_service_url"], 
                        action="store", 
                        type=str, 
                        nargs='?', 
                        required=False)
    parser.add_argument("--handle_service_url", 
                        help=script_details["Args"]["handle_service_url"], 
                        action="store", 
                        type=str, 
                        nargs="?", 
                        required=False)
    parser.add_argument("--working_directory", 
                        help=script_details["Args"]["working_directory"], 
                        action="store", 
                        type=str, 
                        nargs='?', 
                        required=True)
    
    args, unknown = args.parse_known_args()
    
    logger = script_utils.stderrlogger(__file__)
    
    try:
        transform(shock_service_url=args.shock_service_url,
                  handle_service_url=args.handle_service_url,
                  working_directory=args.working_directory,
                  logger = logger)
    except Exception, e:
        logger.exception(e)
        sys.exit(1)
    
    sys.exit(0)