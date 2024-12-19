import os
import ROOT
import commonTools
import latinoTools
import combineTools
import copy
import math
import ctypes
from array import array

### Analysis defaults

def setAnalysisDefaults(opt):

    opt.baseDir = os.getenv('PWD')
    opt.combineLocation = 'XXX/CMSSW_14_1_0_pre4/src'

    opt.filesToExec = {}
    if 'XXX' in opt.year:
        opt.filesToExec['samples.py'] = 'samples_XXX.py'

### Shapes

### Plots

### Combine

### Analysis specific weights, efficiencies, scale factors, etc.


