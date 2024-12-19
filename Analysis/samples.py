import os
from mkShapesRDF.lib.search_files import SearchFiles

### Methods

def nanoGetSampleFiles(path, name, treename):
    if skipTreesCheck: return [(name, [ 'dummy.root' ])]
    _files = s.searchFiles(path, treename, redirector=redirector, isLatino=isLatino)
    if limitFiles != -1 and len(_files) > limitFiles:
        return [(name, _files[:limitFiles])]
    else:
        return [(name, _files)]

def addSampleWeight(samples, sampleName, sampleNameType, weight):
    obj = list(filter(lambda k: k[0] == sampleNameType, samples[sampleName]["name"]))[0]
    samples[sampleName]["name"] = list(
        filter(lambda k: k[0] != sampleNameType, samples[sampleName]["name"])
    )
    if len(obj) > 2:
        samples[sampleName]["name"].append(
            (obj[0], obj[1], obj[2] + "*(" + weight + ")")
        )
    else:
        samples[sampleName]["name"].append((obj[0], obj[1], "(" + weight + ")"))

### Process utilities

samples = {}

s = SearchFiles()

isDatacardOrPlot = action=='plots' or action=='datacards' 
isPlot = action=='plots'
isShape = 'shapes' in action
isFillShape = action=='shapes'

redirector = ''
isLatino = False
limitFiles = -1
skipTreesCheck = not isShape

### Sample directories

SITE=os.uname()[1]
if 'cern' not in SITE and 'ifca' not in SITE and 'cloud' not in SITE: SITE = 'cern'

if 'cern' in SITE:
    treeBaseDirMC   = 'XXX'
    treeBaseDirData = 'XXX'
else: print('trees for', campaign, 'campaign available only at cern')

ProductionMC   = campaign
ProductionData = campaign
  
directoryBkg  = '/'.join([ treeBaseDirMC,   ProductionMC  , '' ])
directoryData = '/'.join([ treeBaseDirData, ProductionData, '' ])

### General parameters

CME = '13.6'
lumi = 1. if 'Validation' in tag else 9.451 if 'Summer23BPix' in campaign else 17.650

### Complex variables

### MC

if 'SM' in sigset or 'MC' in sigset:

    print('Add you MC samples year')

    #samples['XXX'] = { 'name' : nanoGetSampleFiles( ... ), 
    #                   'weight' : '1.', 
    #                   'isSignal' : 0 }

    #addSampleWeight( ... )

# Common MC keys

for sample in samples:

    samples[sample]['isDATA']    = 0
    samples[sample]['isFastsim'] = 0
    samples[sample]['suppressNegative']          = ['all']
    samples[sample]['suppressNegativeNuisances'] = ['all']
    samples[sample]['suppressZeroTreeNuisances'] = ['all']
    samples[sample]['JobsPerSample'] = 20*nPtHatBins if 'Light' in tag else 8*nPtHatBins

### Data

if 'SM' in sigset or 'Data' in sigset:

    print('Add you data samples year')

    #samples['DATA']  = { 'name'      : nanoGetSampleFiles( ... ),
    #                     'weight'    : '1.' ,
    #                     'isData'    : ['all'] ,
    #                     'isSignal'  : 0 ,
    #                     'isDATA'    : 1 ,
    #                     'isFastsim' : 0 ,
    #                     'JobsPerSample' : 10,
    #                    }
     
### Files per job

for sample in samples:
    if 'FilesPerJob' not in samples[sample] and 'JobsPerSample' in samples[sample]:
        ntrees = 0
        for sampleType in samples[sample]['name']: ntrees += len(sampleType[1])
        multFactor = int(samples[sample]['JobsPerSample'])
        samples[sample]['FilesPerJob'] = int(math.ceil(float(ntrees)/multFactor))

### Cleaning

if sigset.split('-')[0] not in [ 'SM', 'MC', 'Data' ]:

    sampleToRemove = [ ]

    shortset = sigset.split('-')[0]

    for sample in samples:
        if 'Veto' in shortset:
            if sample in shortset:
                sampleToRemove.append(sample)
        elif sample not in shortset: # Be sure this sample's name is not substring of other samples' names
            sampleToRemove.append(sample)

    for sample in sampleToRemove:
        del samples[sample]

