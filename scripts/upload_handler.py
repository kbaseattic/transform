#!/usr/bin/python
import argparse
import sys
import os
import time
import traceback
import sys
import ctypes
import subprocess
from subprocess import Popen, PIPE
import os
from optparse import OptionParser
from biokbase.workspace.client import Workspace

desc1 = '''
NAME
      upload_handler -- upload data into WS.

SYNOPSIS      
      
'''

desc2 = '''
DESCRIPTION
  upload_handler call actual uploader script to upload user data stored in Shock into KBase workspace.
'''

desc3 = '''
EXAMPLES
      Filter genes with ANOVA
      > upload_handler --ws_url 'https://kbase.us/services/ws' --ws_id KBasePublicExpression  --in_id 'my_series' --out_id 'filtered_series' --method anova --p_value 0.01 
      > upload_handler -u 'https://kbase.us/services/ws' -w KBasePublicExpression  -i 'my_series' -o 'filtered_series' -m anova -p 0.01 
      
      Filter genes with LOR
      > upload_handler --ws_url 'https://kbase.us/services/ws' --ws_id KBasePublicExpression  --in_id 'my_series' -out_id 'filtered_series' --method lor --p_value 0.01 
      > upload_handler -u 'https://kbase.us/services/ws' -w KBasePublicExpression  -i 'my_series' -o 'filtered_series' -m lor -p 0.01


SEE ALSO
      validator_handler, import_handler

AUTHORS
First Last.
'''


def handler (args) :
    ###
    # download ws object and convert them to csv
    wsd = Workspace(url=args.ws_url, token=os.environ.get('KB_AUTH_TOKEN'))
    indata = wsd.get_object({'id' : args.inobj_id,
                  #'type' : 'KBaseExpression.ExpressionSeries', 
                  'workspace' : args.ws_id})['data']

    if indata is None:
        raise Exception("Object {} not found in workspace {}".format(args.inobj_id, args.ws_id))


    ###
    # execute filtering
    flt_cmd_lst = ['mys_example', "-i", "{}-{}".format(os.getpid(),args.exp_fn) ]
    if (args.method     is not None): 
        flt_cmd_lst.append('-m')
        flt_cmd_lst.append(args.method)
    if (args.p_value    is not None): 
        flt_cmd_lst.append('-p')
        flt_cmd_lst.append(args.p_value)
    if (args.num_genes  is not None): 
        flt_cmd_lst.append('-n')
        flt_cmd_lst.append(args.num_genes)
    if (args.flt_out_fn is not None): 
        flt_cmd_lst.append('-o')
        flt_cmd_lst.append("{}-{}".format(os.getpid(),args.flt_out_fn))

    p1 = Popen(flt_cmd_lst, stdout=PIPE)
    out_str = p1.communicate()
    # print output message for error tracking
    if out_str[0] is not None : print out_str[0]
    if out_str[1] is not None : print >> sys.stderr, out_str[1]
    flt_cmd = " ".join(flt_cmd_lst)
   
    ###
    # put it back to workspace
    #fif = open("{}-{}".format(os.getpid(),args.flt_out_fn), 'r')
    #fif.readline(); # skip header
    
    # assume only one genome id
    outdata = {}
    outdata['key'] = indata['key']
    outdata['value'] = "{}{}".format(indata['value'], indata['value'])
    data_list = []
    data_list.append({'type' : 'MyService.PairString', 'data' : outdata, 'name' : args.outobj_id, 'meta' : {'org.series' : args.inobj_id}})
    wsd.save_objects({'workspace' : args.ws_id, 'objects' : data_list})

    if(args.del_tmps is "true") :
        os.remove("{}-{}".format(os.getpid(), args.exp_fn))
        os.remove("{}-{}".format(os.getpid(), args.flt_out_fn))

if __name__ == "__main__":
    # Parse options.
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter, prog='upload_handler', epilog=desc3)
    parser.add_argument('-u', '--ws_url', help='Workspace url', action='store', dest='ws_url', default='https://kbase.us/services/ws')
    parser.add_argument('-s', '--shock_url', help='Shock url', action='store', dest='shock_url', default='https://kbase.us/services/shock-api')
    parser.add_argument('-w', '--ws_name', help='Workspace name', action='store', dest='ws_id', default=None, required=True)
    parser.add_argument('-i', '--in_id', help='Input Shock node id', action='store', dest='inobj_id', default=None, required=True)
    parser.add_argument('-o', '--out_id', help='Output WS object id', action='store', dest='outobj_id', default=None, required=True)
    parser.add_argument('-e', '--e_type', help='External object type', action='store', dest='e_type', default=None, required=True)
    parser.add_argument('-k', '--kb_type', help='KBase object type', action='store', dest='kb_type', default=None, required=True)
    parser.add_argument('-b', '--script_dir', help='Script directory', action='store', dest='sdir', default='bin')
    parser.add_argument('-d', '--del_script_dir', help='Delete script directory', action='store', dest='del_tmps', default='false')
    usage = parser.format_usage()
    parser.description = desc1 + '      ' + usage + desc2
    parser.usage = argparse.SUPPRESS
    args = parser.parse_args()

    if(args.p_value is None and args.num_genes is None) :
        print "Either p_value or num_genes has to be specified";
        exit(1);

    # main loop
    handler(args)
    exit(0);
