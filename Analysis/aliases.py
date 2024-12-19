import os
import json
import datetime
from array import array

aliases = OrderedDict()

dataDir = '/'.join([ os.path.abspath('Data'), campaign ])
macrosPath = os.path.abspath('macros')

mc   = [ x for x in samples if not samples[x]['isDATA'] ]
data = [ x for x in samples if samples[x]['isDATA'] ]



