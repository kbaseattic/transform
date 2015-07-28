#!/usr/bin/env python

# standard library imports
import os
import sys
import logging
import argparse
import subprocess

# 3rd party imports

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
              genome_object_name=None, fill_missing_values=None, data_type=None, 
              data_scale=None, level=logging.INFO, logger=None):
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
        fill_missing_values: Flag for filling in missing values in matrix (0-false, 1-true).
        data_type: Data type (default value is 'log-ratio').
        data_scale: Data scale (default value is '1.0').

    Returns:
        JSON files on disk that can be saved as a KBase workspace objects.

    Authors:
        Roman Sutormin
    """

    if logger is None:
        logger = script_utils.stderrlogger(__file__)

    logger.info("Starting conversion of Expression TSV to KBaseFeatureValues.ExpressionMatrix")
    # token = os.environ.get('KB_AUTH_TOKEN')

    if not working_directory or not os.path.isdir(working_directory):
        raise Exception("The working directory {0} is not a valid directory!"
                        .format(working_directory))

    classpath = ["$KB_TOP/lib/jars/kbase/feature_values/kbase-feature-values-0.2.jar",
                 "$KB_TOP/lib/jars/kohsuke/args4j-2.0.21.jar",
                 "$KB_TOP/lib/jars/kbase/common/kbase-common-0.0.10.jar",
                 "$KB_TOP/lib/jars/jackson/jackson-annotations-2.2.3.jar",
                 "$KB_TOP/lib/jars/jackson/jackson-core-2.2.3.jar",
                 "$KB_TOP/lib/jars/jackson/jackson-databind-2.2.3.jar",
                 "$KB_TOP/lib/jars/kbase/auth/kbase-auth-1398468950-3552bb2.jar",
                 "$KB_TOP/lib/jars/kbase/workspace/WorkspaceClient-0.2.0.jar"]
    
    mc = "us.kbase.kbasefeaturevalues.transform.ExpressionUploader"

    argslist = ["--workspace_service_url {0}".format(workspace_service_url),
                "--workspace_name {0}".format(workspace_name),
                "--object_name {0}".format(object_name),
                "--input_directory {0}".format(input_directory),
                "--working_directory {0}".format(working_directory)]
    if output_file_name:
        argslist.append("--output_file_name {0}".format(output_file_name))
    if input_mapping:
        argslist.append("--input_mapping {0}".format(input_mapping))
    if format_type:
        argslist.append("--format_type {0}".format(format_type))
    if genome_object_name:
        argslist.append("--genome_object_name {0}".format(genome_object_name))
    if fill_missing_values:
        argslist.append("--fill_missing_values")
    if data_type:
        argslist.append("--data_type {0}".format(data_type))
    if data_scale:
        argslist.append("--data_scale {0}".format(data_scale))

    arguments = ["java", "-classpath", ":".join(classpath), mc, " ".join(argslist)]

    logger.debug(arguments)

    # need shell in this case because the java code is depending on finding the KBase token in the environment
    tool_process = subprocess.Popen(" ".join(arguments), stderr=subprocess.PIPE, shell=True)
    stdout, stderr = tool_process.communicate()

    if stdout is not None and len(stdout) > 0:
        logger.info(stdout)

    if stderr is not None and len(stderr) > 0:
        logger.error("Transformation from TSV.Expression to KBaseFeatureValues.ExpressionMatrix failed on {0}".format(input_directory))
        logger.error(stderr)
        sys.exit(1)

    logger.info("Conversion completed.")


def main():
    script_details = script_utils.parse_docs(transform.__doc__)

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
    parser.add_argument('--fill_missing_values',
                        help=script_details["Args"]["fill_missing_values"],
                        action='store', type=int, required=False)
    parser.add_argument('--data_type',
                        help=script_details["Args"]["data_type"],
                        action='store', type=str, required=False)
    parser.add_argument('--data_scale',
                        help=script_details["Args"]["data_scale"],
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
                  fill_missing_values=args.fill_missing_values,
                  data_type=args.data_type,
                  data_scale=args.data_scale,
                  logger=logger)
    except Exception as e:
        logger.exception(e)
        sys.exit(1)


# called only if script is run from command line
if __name__ == "__main__":  # pragma: no cover
    main()

