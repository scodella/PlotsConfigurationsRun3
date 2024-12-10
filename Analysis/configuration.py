# Configuration file

runnerFile = 'default'

# used by mkShape to define output directory for root files
outputFile    = 'mkShapes.root'
outputFolder  = './Shapes'

batchFolder   = 'condor'
configsFolder = 'configs'

# file with TTree aliases
aliasesFile = 'aliases.py'

# file with list of variables
variablesFile = 'variables.py'

# file with list of cuts
cutsFile = 'cuts.py' 

# file with list of samples
samplesFile = 'samples.py' 

# file with list of samples
plotFile = 'plot.py' 

# used by mkPlot to define output directory for plots
# different from "outputDir" to do things more tidy
plotPath = './Plots'

# used by mkDatacards to define output directory for datacards
outputDirDatacard = 'Datacards'

# structure file for datacard
structureFile = 'structure.py'

# nuisances file for mkDatacards and for mkShape
nuisancesFile = 'nuisances.py'

minRatio = 0.5
maxRatio = 1.5
plotPath = 'plots'

mountEOS=[]

imports = ["os", "glob", ("collections", "OrderedDict"), "ROOT"]

filesToExec = [
    samplesFile,
    aliasesFile,
    cutsFile,
    variablesFile,
    plotFile,
    nuisancesFile,
    structureFile,
]

varsToKeep = [
    "batchVars",
    "outputFolder",
    "batchFolder",
    "configsFolder",
    "outputFile",
    "runnerFile",
    "year",
    "tag",
    "sigset",
    "samples",
    "aliases",
    "variables",
    ("cuts", {"cuts": "cuts", "preselections": "preselections"}),
    ("plot", {"plot": "plot", "groupPlot": "groupPlot", "legend": "legend"}),
    "nuisances",
    "structure",
    "treeName",
    "lumi",
    "mountEOS",
]

batchVars = varsToKeep[varsToKeep.index("samples") :]

varsToKeep += ['minRatio', 'maxRatio', 'plotPath']
