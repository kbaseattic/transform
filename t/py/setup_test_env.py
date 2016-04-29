#!/usr/bin/env python
'''
Created on Feb 4, 2015

@author: gaprice@lbl.gov
'''
import os
import sys

FILE_LOC = os.path.split(__file__)[0]

sys.path.append(os.path.join(FILE_LOC, '../'))  # to import demo/setup
# this import is both resolved and used
from demo.setup import TransformVirtualEnv  # @UnresolvedImport @UnusedImport @IgnorePep8

TRANSFORM_LOC = os.path.join(FILE_LOC, '../../')

TransformVirtualEnv(FILE_LOC, 'venv', TRANSFORM_LOC)
