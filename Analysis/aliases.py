##### aliases = {}

import os

includePath = 'gSystem->AddIncludePath("-I%s/src/");' % os.getenv('CMSSW_RELEASE_BASE')
aliasDir = os.getenv('PWD')+'/aliases'

## Example
#aliases['myalias'] = { 'linesToAdd': [ includePath, '.L '+aliasDir+'/myaliasscript.cc+' ],
#                       'class': 'myaliasclass',
#                       'args': ( 'arg1', 'arg2', 'arg3' ),
#                       'samples': [ 'sample1', 'sample2', 'samples3' ]
#                      }

