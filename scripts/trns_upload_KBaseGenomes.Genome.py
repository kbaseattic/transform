#!/usr/bin/env python

import argparse
import sys
import os
import time
import traceback
import sys
import shutil
from optparse import OptionParser
from biokbase.workspace.client import Workspace
import json
from biokbase import log
from biokbase.userandjobstate.client import UserAndJobState
from biokbase.Transform.util import Uploader
import datetime
from os import listdir
import re

desc1 = '''
NAME
      trns_upload_KBaseGenomes.Genome -- upload the input data into WS

SYNOPSIS      
      
'''

desc2 = '''
DESCRIPTION
  trns_upload_KBaseGenomes.Genome upload the input data into WS
  
'''

desc3 = '''
EXAMPLES
      CSV test case
      > trns_upload_KBaseGenomes.Genome --ws_url 'https://kbase.us/services/ws' --ws_id kbasetest:home  --in_id '' --out_id 'my_tst_out'
      
      Filter genes with LOR
      > trns_upload_KBaseGenomes.Genome --ws_url 'https://kbase.us/services/ws' --ws_id KBasePublicExpression  --in_id '' -out_id 'my_tst_out'


SEE ALSO
      trns_validate_hndlr, trns_import_hndlr

AUTHORS
First Last.
'''

if __name__ == "__main__":
    # Parse options.
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter, prog='trns_upload_KBaseGenomes.Genome', epilog=desc3)
    parser.add_argument('-u', '--ws_url', help='Workspace url', action='store', dest='ws_url', default='https://kbase.us/services/ws', required=True)

    parser.add_argument('-w', '--dst_ws_name', help='Destination workspace name', action='store', dest='ws_id', default=None, required=True)
    parser.add_argument('-o', '--out_id', help='Output workspace object name', action='store', dest='outobj_id', default=None, required=True)

    parser.add_argument('-l', '--support_dir', help='Support directory', action='store', dest='sdir', default='lib', required=True)
    parser.add_argument('-g', '--out_file', help='Output prefix or file name', action='store', dest='otmp', default='outfile', required=False)
    # for meta data
    parser.add_argument('-i', '--in_id', help='Input Shock node id for meta', action='store', dest='inobj_id', default='NotProvided', required=True)
    parser.add_argument('-e', '--ext_type', help='External object type', action='store', dest='etype', default=None, required=True)
    parser.add_argument('-j', '--job_id', help='UJS job id', action='store', dest='jid', default='NoJodID', required=False)

    usage = parser.format_usage()
    parser.description = desc1 + '      ' + usage + desc2
    parser.usage = argparse.SUPPRESS
    args = parser.parse_args()

    
    kb_token = os.environ.get('KB_AUTH_TOKEN')
    wsd = Workspace(url=args.ws_url, token=kb_token)

    gids = [ re.sub(r"_ContigSet.jsonp$","", f) for f in listdir(".") if f.endswith("_ContigSet.jsonp")]


    ## main loop
    for gid in gids:
      # store contigset first
      jif = open("{}/{}_ContigSet.jsonp".format(".",gid, 'r'))
      data = json.loads(jif.read())
      jif.close()
      
      wsd.save_objects({'workspace':args.ws_id, 'objects' : [ {
        'type' : 'KBaseGenomes.ContigSet', 'data' : data, 'name' : "{}-{}_cs".format(args.outobj_id, gid), 
        'meta' : { 'source_id' : args.inobj_id, 'source_type' : args.etype,
                   'ujs_job_id' : args.jid} } ]})
      
      jif = open("{}/{}.jsonp".format(".",gid, 'r'))
      data = json.loads(jif.read())
      jif.close()
      
      data['contigset_ref'] = "{}/{}-{}_cs".format(args.ws_id,args.outobj_id, gid)


      wsd.save_objects({'workspace':args.ws_id, 'objects' : [ {
        'type' : 'KBaseGenomes.Genome', 'data' : data, 'name' : "{}-{}_gn".format(args.outobj_id, gid), 
        'meta' : { 'source_id' : args.inobj_id, 'source_type' : args.etype,
                   'ujs_job_id' : args.jid} } ]})

    exit(0);
