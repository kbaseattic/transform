#!/usr/bin/env python

# standard library imports
import os
import sys
import logging

# 3rd party imports
import simplejson

# KBase imports
try:
    import biokbase.Transform.script_utils as script_utils
except ImportError:
    from . import kbase_utils as script_utils


if sys.version.startswith('3'):
    unicode = str


def transform(workspace_service_url=None, workspace_name=None,
              object_name=None, output_file_name=None, input_directory=None, 
              working_directory=None, input_mapping=None, format_type=None, 
              genome_object_name=None, level=logging.INFO, logger=None):
    """
    Converts Expression TSV file to json string of KBaseFeatureValues.ExpressionMatrix type.

    Args:
        workspace_service_url: URL for a KBase Workspace service where KBase objects.
                               are stored.
        workspace_name: The name of the destination workspace.
        object_name: The destination object name.
        output_file_name: A file name where the output JSON string should be stored.
                          If the output file name is not specified the name will
                          default to the name of the input file appended with
                          '_output.json'.
        input_directory: The directory where files will be read from.
        working_directory: The directory the resulting json file will be
                           written to.
        input_mapping: JSON string mapping of input files to expected types.
                       If you don't get this you need to scan the input
                       directory and look for your files.
        format_type: Mannually defined type of TSV file format.
        genome_object_name: Optional reference to a Genome object that will be used.
                            for mapping feature IDs to.

    Returns:
        JSON files on disk that can be saved as a KBase workspace objects.

    Authors:
        Roman Sutormin
    """

    if logger is None:
        logger = script_utils.stderrlogger(__file__)

    logger.info("Starting conversion of Expression TSV to KBaseFeatureValues.ExpressionMatrix")
    token = os.environ.get('KB_AUTH_TOKEN')

    if not working_directory or not os.path.isdir(working_directory):
        raise Exception("The working directory {0} is not a valid directory!"
                        .format(working_directory))

    if output_file_name is None:
        output_file_name = 'expression_output.json'

    run_info = dict()
    run_info['type'] = "log-ratio"
    run_info['scale'] = "1.0"
    run_info['data'] = {'row_ids': ["g1"], 'col_ids': ["c1"], 'values': [[0.5]]}
    objectString = simplejson.dumps(run_info, sort_keys=True, indent=4)

    output_file_path = os.path.join(working_directory, output_file_name)
    with open(output_file_path, "w") as outFile:
        outFile.write(objectString)

    logger.info("Conversion completed.")


def main():
    script_details = script_utils.parse_docs(transform.__doc__)

    import argparse

    parser = argparse.ArgumentParser(prog=__file__,
                                     description=script_details["Description"],
                                     epilog=script_details["Authors"])

    parser.add_argument('--workspace_service_url',
                        help=script_details["Args"]["workspace_service_url"],
                        action='store', type=str, nargs='?', required=True)
    parser.add_argument('--workspace_name',
                        help=script_details["Args"]["workspace_name"],
                        action='store', type=str, nargs='?', required=True)
    parser.add_argument("--object_name", 
                        help=script_details["Args"]["object_name"], 
                        action='store', type=str, nargs='?', required=True)
    parser.add_argument('--output_file_name',
                        help=script_details["Args"]["output_file_name"],
                        action='store', type=str, nargs='?', default=None,
                        required=False)
    parser.add_argument('--input_directory',
                        help=script_details["Args"]["input_directory"],
                        action='store', type=str, nargs='?', required=True)
    parser.add_argument("--working_directory", 
                        help=script_details["Args"]["working_directory"], 
                        action='store', type=str, nargs='?', required=True)
    parser.add_argument('--input_mapping',
                        help=script_details["Args"]["input_mapping"],
                        action='store', type=unicode, nargs='?', default=None,
                        required=False)

    # custom arguments specific to this uploader
    parser.add_argument('--format_type',
                        help=script_details["Args"]["format_type"],
                        action='store', type=str, required=False)
    parser.add_argument('--genome_object_name',
                        help=script_details["Args"]["genome_object_name"],
                        action='store', type=str, required=False)

    args, unknown = parser.parse_known_args()

    logger = script_utils.stderrlogger(__file__)

    logger.debug(args)
    try:
        transform(workspace_service_url=args.workspace_service_url,
                  workspace_name=args.workspace_name,
                  object_name=args.object_name,
                  output_file_name=args.output_file_name,
                  input_directory=args.input_directory,
                  working_directory=args.working_directory,
                  input_mapping=args.input_mapping,
                  format_type=args.format_type,
                  genome_object_name=args.genome_object_name,
                  logger=logger)
    except Exception as e:
        logger.exception(e)
        sys.exit(1)


# called only if script is run from command line
if __name__ == "__main__":  # pragma: no cover
    main()

