import os
import glob
import copy
import ROOT
import subprocess
import json
import math
from array import array
#import LatinoAnalysis.ShapeAnalysis.tdrStyle as tdrStyle

### General utilities

#tdrStyle.setTDRStyle()

class Object(object):
    pass

def getBranch():

    proc=subprocess.Popen('git branch', stderr = subprocess.PIPE,stdout = subprocess.PIPE, shell = True)
    out, err = proc.communicate()

    for line in out.split("\n"): 
        if '*' in line:
            return line.replace('* ','')

def isGoodFile(filename, minSize=100000.):

    if not os.path.isfile(filename): return False
    fileSize = os.path.getsize(filename)
    return fileSize>minSize

def hasString(filename, string):

    with open(filename) as myfile:
        if string in myfile.read(): return True
    return False

def compile(opt):
  
    if 'base' in opt.option.lower(): directory = '$CMSSW_BASE/src/' 
    elif 'tool' in opt.option.lower() or opt.option=='': directory = '$CMSSW_BASE/src/PlotsConfigurations/Tools/'
    elif 'latino' in opt.option.lower(): directory = '$CMSSW_BASE/src/LatinoAnalysis/'
    else: directory = opt.option
    os.system('cd '+directory+' ; scram b')

def cdWorkDir(opt, workdir = os.getenv('PWD')):

    return 'cd '+workdir+'; eval `scramv1 runtime -sh`; cd - '

def loadJSON(jsonFile):

    return json.load(open(jsonFile, 'r'))

### Math formulas

def statisticalCompatibility(a, ea, b, eb):

    diff = a-b
    errDiff = math.sqrt(ea*ea+eb*eb)
    return diff/errDiff

### Plot utilities

def bookHistogram(name, xBins, yBins=(), title='', style=''):

    if len(yBins)==0:
        if len(xBins)==1:
            histogram = ROOT.TH1F(name, title, len(xBins[0])-1, array('d',xBins[0]))
        elif len(xBins)==3:
            histogram = ROOT.TH1F(name, title, xBins[0], xBins[1], xBins[2])
    elif len(yBins)==1:
        if len(xBins)==1:
            histogram = ROOT.TH2F(name, title, len(xBins[0])-1, array('d',xBins[0]), len(yBins[0])-1, array('d',yBins[0]))
        elif len(xBins)==3:
            histogram = ROOT.TH2F(name, title, xBins[0], xBins[1], xBins[2], len(yBins[0])-1, array('d',yBins[0]))
    elif len(yBins)==3:
        if len(xBins)==1:
            histogram = ROOT.TH2F(name, title, len(xBins[0])-1, array('d',xBins[0]), yBins[0], yBins[1], yBins[2])
        elif len(xBins)==3:
            histogram = ROOT.TH2F(name, title, xBins[0], xBins[1], xBins[2], yBins[0], yBins[1], yBins[2])

    histogram.SetTitle('')

    #histogram.GetXaxis().SetLabelFont(42)
    #histogram.GetYaxis().SetLabelFont(42)
    #histogram.GetXaxis().SetTitleFont(42)
    #histogram.GetYaxis().SetTitleFont(42)

    if style=='btv':

        histogram.GetXaxis().SetLabelSize(0.05)
        histogram.GetYaxis().SetLabelSize(0.05)
        histogram.GetXaxis().SetTitleSize(0.06)
        histogram.GetYaxis().SetTitleSize(0.06)

        histogram.GetXaxis().SetLabelOffset(0.015)
        histogram.GetYaxis().SetLabelOffset(0.01)
        histogram.GetXaxis().SetTitleOffset(0.95)
        histogram.GetYaxis().SetTitleOffset(1.25)

    elif style=='latino':

        histogram.GetXaxis().SetLabelSize(0.035)
        histogram.GetYaxis().SetLabelSize(0.035)
        histogram.GetXaxis().SetTitleSize(0.035)
        histogram.GetYaxis().SetTitleSize(0.045)

        histogram.GetXaxis().SetLabelOffset(0.015)
        histogram.GetYaxis().SetLabelOffset(0.01)
        histogram.GetXaxis().SetTitleOffset(1.35)
        histogram.GetYaxis().SetTitleOffset(1.55)

        histogram.GetXaxis().SetNdivisions(505)
        histogram.GetYaxis().SetNdivisions(505)

    return histogram

def bookCanvas(name, xSize, ySize, title=''):

    canvas = ROOT.TCanvas(name, title, xSize, ySize)

    canvas.Range(0,0,1,1)

    #canvas.SetFillColor(10)
    #canvas.SetFillStyle(4000)

    #canvas.SetBorderMode(0)
    #canvas.SetBorderSize(2)

    #canvas.SetTickx(1)
    #canvas.SetTicky(1)

    #canvas.SetLeftMargin(0.16)
    #canvas.SetRightMargin(0.02)
    #canvas.SetTopMargin(0.05)
    #canvas.SetBottomMargin(0.13)

    #canvas.SetFrameFillColor(0)
    #canvas.SetFrameFillStyle(0)
    #canvas.SetFrameBorderMode(0)

    return canvas

def bookPad(name, xlow, ylow, xup, yup, title=''):

    pad = ROOT.TPad(name, title, xlow, ylow, xup, yup)

    #pad.SetFillColor(0)

    #pad.SetBorderMode(0)
    #pad.SetBorderSize(2)

    #pad.SetTickx(1)
    #pad.SetTicky(1)

    #pad.SetLeftMargin(0.16)
    #pad.SetRightMargin(0.02)
    #pad.SetTopMargin(0.065)
    #pad.SetBottomMargin(0.13)

    #pad.SetFrameFillColor(0)
    #pad.SetFrameFillStyle(0)
    #pad.SetFrameBorderMode(0)

    return pad

### Configurations

from pathlib import Path
from mkShapesRDF.shapeAnalysis.ConfigLib import ConfigLib

def compileConfigurations(opt, action, year='', tag='', sigset='', fileset='', configsFolder='', plotPath='', varsToRead=[], fitoption=''):

    ConfigLib.loadConfig([opt.configuration], globals())

    year, tag, sigset = getYearTagSigset(opt, year, tag, sigset)

    if not opt.interactive and '"' not in opt.treeName: opt.treeName = '"'+opt.treeName+'"'
    globals()['treeName'] = opt.treeName
    globals()['action'] = action
    globals()['sigset'] = sigset
    globals()['plotPath'] = opt.plotsdir if plotPath=='' else plotPath

    if hasattr(opt, 'filesToExec'):
        for fileToExec in list(opt.filesToExec.keys()):
            fileIndex = filesToExec.index(fileToExec)
            filesToExec[fileIndex] = opt.filesToExec[fileToExec]

    global folder
    folder = os.getenv('PWD')
    varsToKeep.insert(0, 'folder')
    for varToRead in varsToRead:
        if varToRead not in varsToKeep:
            varsToKeep.append(varToRead)

    import datetime
    dt = datetime.datetime.now()

    globals()['batchFolder'] = '/'.join([ opt.batchFolder, 'mkShapes', year ])
    globals()['year'], globals()['tag'] = year, tag
    splitSubFolder = fitoption if 'shapes' not in action else 'Test' if opt.interactive else 'Split'
    globals()['outputFolder'] = getShapeDirName(opt.shapedir, year, tag, splitSubFolder)
    globals()['outputFile'] = getShapeLocalFileName(tag, '' if 'shapes' in action else sigset, fileset, fitoption)
    ConfigLib.loadConfig(filesToExec, globals(), imports)

    d = ConfigLib.createConfigDict( varsToKeep, dict(list(globals().items()) + list(locals().items())) )

    configName = '/config'+'_'.join([ action, year, tag, sigset, dt.strftime('%y-%m-%d_%H_%M_%S') ])
    if configsFolder=='': configsFolder = opt.configsFolder

    Path(configsFolder).mkdir(parents=True, exist_ok=True)
    fileName = configsFolder + configName
    ConfigLib.dumpConfigDict(d, fileName)

    return fileName + '.pkl'

def getConfigParameters(opt, varsToRead, configFile=''):

    if configFile=='':
        deleteConfigFile = True
        configFile = compileConfigurations(opt, 'getConfigParameters', varsToRead=varsToRead)
    else: deleteConfigFile = False

    d = ConfigLib.loadPickle(configFile, globals())

    for attribute in varsToRead:
        setattr(opt, attribute, globals()[attribute])

    if deleteConfigFile: cleanConfigs(opt, configFile)

def getDictionaries(opt, lastDictionary='nuisances', configFile=''):

    dictionaryList = [ 'samples', 'cuts', 'variables', 'nuisances' ]
    dictionariesToRead = [ x for x in dictionaryList if dictionaryList.index(x)<=dictionaryList.index(lastDictionary) ]

    optAux = copy.deepcopy(opt)
    getConfigParameters(optAux, dictionariesToRead, configFile)

    if   lastDictionary=='samples':    return optAux.samples
    elif lastDictionary=='cuts':       return optAux.samples, optAux.cuts
    elif lastDictionary=='variables' : return optAux.samples, optAux.cuts, optAux.variables
    elif lastDictionary=='nuisances' : return optAux.samples, optAux.cuts, optAux.variables, optAux.nuisances

def getDictionariesInLoop(opt, year, tag, sigset, lastDictionary='nuisances', configFile=''):

    optAux = setOptYearTagSigset(opt, year, tag, sigset)
    return getDictionaries(optAux, lastDictionary, configFile)

def getSamples(opt, year='', tag='', sigset=''):

    return getDictionariesInLoop(opt, year, tag, sigset, 'samples')

def getSignalList(opt, year='', tag='', sigset=''):

    samples = getSamples(opt, year, tag, sigset)
    return [ x for x in samples if samples[x]['isSignal'] ]

### Some random utilities

def getYearTagSigset(opt, year='', tag='', sigset=''):

    if year=='':   year = opt.year
    if tag=='':    tag = opt.tag
    if sigset=='': sigset = opt.sigset
    return year, tag, sigset

def setOptYearTagSigset(opt, year='', tag='', sigset=''):

    optOut = copy.deepcopy(opt)
    optOut.year, optOut.tag, optOut.sigset = getYearTagSigset(opt, year, tag, sigset)
    return optOut

def getFileset(fileset, sigset):

    if fileset=='': fileset = sigset
    while(fileset[0]=='_'): fileset = fileset[1:]
    return fileset

def getFilesetForShapesName(fileset, sigset):

    filesetForShapesName = getFileset(fileset, sigset)
    if filesetForShapesName=='': return ''
    else: return '__'+filesetForShapesName

def getTagForDatacards(tag, sigset):

    flagsToAppend = []
    for fl in range(len(sigset.split('_')[0].split('-'))-1):
        if sigset.split('-')[fl]!='SM' and sigset.split('-')[fl] not in tag: flagsToAppend.append(sigset.split('-')[fl])

    if len(flagsToAppend)!=0:
        rawtag = tag.split('_')[0]
        tag = tag.replace(rawtag, rawtag+'_'+'_'.join([ x for x in flagsToAppend ]))

    return tag

def getPerSignalSigset(fileset, sigset, signal):

    fileset = getFileset(fileset, sigset)
    if 'SM-' in fileset: return 'SM-'+signal       # This is SUSY like
    elif sigset=='' or sigset=='SM': return sigset # This should work for SM searches
    else: return signal                            # Guessing latinos' usage

def getSignalDir(opt, year, tag, signal, directory=''):

    if directory=='': directory = 'combineOutDir'

    if hasattr(opt, 'combineOutDir') and opt.combineOutDir.split('/')[-1]==opt.cardsdir.split('/')[-1]:
        signalDirList = [ getattr(opt, directory), tag, year ]
        if opt.sigset!='' and opt.sigset!='SM': signalDirList.insert(2, signal)

    else:
        signalDirList = [ getattr(opt, directory), year ]
        tag = tag.replace('___','_')
        if '__' in tag: signalDirList.append(tag.replace('__','/'))
        else: signalDirList.append(tag) 
        if opt.sigset!='' and opt.sigset!='SM': signalDirList.append(signal)

    return '/'.join(signalDirList)

def isExotics(opt):

    return hasattr(opt, 'isExotics') and opt.isExotics

def plotAsExotics(opt):

    if 'notexotics' in opt.option.lower() or 'postfits' in opt.option.lower(): return False
    else: return isExotics(opt) or 'isexotics' in opt.option.lower()

def getAbsPath(relativePath):

    return os.path.abspath(relativePath)

def joinPaths(mainPath, relativePath):

    return os.path.join(mainPath, relativePath)

def mergeDirPaths(baseDir, relDir):

    return getAbsPath(joinPaths(baseDir, relDir))

def copyFileToFolders(file, folders, reffolder='.'):

    os.system('mkdir -p '+folders)
    absPath = getAbsPath(folders)
    refPath = getAbsPath(reffolder)
    commonPath = os.path.commonprefix([absPath, refPath])
    if commonPath!=refPath: 
        print('error in copyFileToFolders:', folders, 'is not a subfolder of', reffolder)
        exit()
    for subdir in os.path.relpath(absPath, refPath).split('/'):
        commonPath += '/'+subdir
        os.system('cp '+file+' '+commonPath)

def buildExternalScript(outputFile, externalScriptCommandList, output):

    outputFile = getAbsPath(outputFile)
    scriptCommandList = [ 'echo "#!/bin/bash" > '+outputFile ]
    scriptCommandList.append('echo "source /cvmfs/cms.cern.ch/cmsset_default.sh" >> '+outputFile)

    for command in externalScriptCommandList:
        scriptCommandList.append('echo "'+command+'" >> '+outputFile)

    scriptCommandList.append('chmod a+x '+outputFile)

    if output=='list': return scriptCommandList
    elif output=='string': return '\n'.join(scriptCommandList)
    elif output=='write': os.system('\n'.join(scriptCommandList))

### Tools to check or clean configs, logs, shapes, plots, datacards and jobs

def deleteDirectory(directory, force, dryRun=False):

    if '/*/' in directory or directory[len(directory)-2:]=='/*':
        if not force:
            print('Please, use --force if you want to delete a * directory')
            exit()

    while directory[len(directory)-1:]=='/':
        directory = directory[:len(directory)-1]
    while directory[len(directory)-2:]=='/*':
        directory = directory[:len(directory)-2]

    deleteCommand = 'rm -r -f '+directory

    if dryRun: return deleteCommand
    else: os.system(deleteCommand)

# configs

def cleanConfigs(opt, configName='', configList=[], force=False):

    if opt.force: force = True
    if configName!='': configList.append(configName)
    if len(configList)>0:
        for configName in configList: 
            deleteDirectory(configName, force)
    elif force:
        deleteDirectory(opt.configsFolder+'/**', force)

# logs

def getLogDirName(batchFolder, job, year, tag):

    return '/'.join([ batchFolder, job, year, tag ])

def cleanLogs(opt, job, year='', tag='', sample = ''):

    year, tag, sigset = getYearTagSigset(opt, year, tag)

    logdir = getLogDirName(opt.batchFolder, job, year, tag)
    if sample!='': logdir += '/'+sample+'*'
    deleteDirectory(logdir, opt.force)

def purgeLogs(opt):

    if not opt.force:
        print('Please, use --force for this action')
        exit

    logdir = opt.batchFolder
    if opt.option!='': logdir += '/'+opt.option
    else: logdir += '/**'
    deleteDirectory(logdir, opt.force)

# shapes

def cleanShapeLogs(opt, year = '', tag = '', sample = ''):

    if year=='': year = opt.year
    if tag=='': tag = opt.tag
    cleanLogs(opt, 'mkShapes', year, tag, sample)

def cleanShapes(opt, year = '', tag = ''):

    if year=='': year = opt.year
    if tag=='': tag = opt.tag
    cleanShapeLogs(opt, year, tag)
    deleteDirectory(getShapeDirName(opt.shapedir, year, tag, 'Split'), opt.force)

def resetShapes(opt, year = '', tag = ''):

    if year=='': year = opt.year
    if tag=='': tag = opt.tag
    cleanShapeLogs(opt, year, tag)
    deleteDirectory(getShapeDirName(opt.shapedir, year, tag), opt.force)

# Datacards

def cleanSignalDatacards(opt, year, tag, signal, dryRun=False):

    cleanSignalDatacardCommandList = []

    for singleYear in year.split('-'):
        cleanSignalDatacardCommandList.append(deleteDirectory(getSignalDir(opt, singleYear, tag, signal, 'cardsdir'),False,True))

    if dryRun: return '\n'.join(cleanSignalDatacardCommandList)
    else: os.system('\n'.join(cleanSignalDatacardCommandList))

# plots

def copyIndexForPlots(plotDir, mainPlotDir='.'):

    copyFileToFolders('../index.php', plotDir, mainPlotDir)

# jobs

def showQueue(opt):

    if 'ifca' in os.uname()[1] or 'cloud' in os.uname()[1]:
        print('\nAvailable queues in slurm:\n cms_main = 24 hours\n cms_med  = 8 hours\n cms_high = 3 hours\n')
    else: #cern
        print('\nAvailable queues in condor:\n espresso     = 20 minutes\n microcentury = 1 hour\n longlunch    = 2 hours\n workday      = 8 hours\n tomorrow     = 1 day\n testmatch    = 3 days\n nextweek     = 1 week\n')

def batchQueue(opt, batchQueue):

    if 'ifca' in os.uname()[1] or 'cloud' in os.uname()[1]:
        if batchQueue not in [ 'cms_main', 'cms_med', 'cms_high' ]:
            if opt.verbose: print('Batch queue', batchQueue, 'not available in gridui. Setting it to cms_high')
            return 'cms_high'
    else: # cern
        if batchQueue not in ['espresso', 'microcentury', 'longlunch', 'workday', 'tomorrow', 'testmatch', 'nextweek' ]:
            if opt.verbose: print('Batch queue', batchQueue, 'not available in lxplus. Setting it to workday')
            return 'workday'

    return batchQueue

def checkProxy(opt):

    cmd='voms-proxy-info'
    proc=subprocess.Popen(cmd, stderr = subprocess.PIPE,stdout = subprocess.PIPE, shell = True)
    out, err = proc.communicate()

    if 'Proxy not found' in err.decode():
        print('WARNING: No GRID proxy -> Get one first with:')
        print('voms-proxy-init -voms cms -rfc --valid 168:0')
        exit()

    timeLeft = 0
    for line in out.decode().split("\n"):
        if 'timeleft' in line : timeLeft = int(line.split(':')[1])

    if timeLeft < 24 :
        print('WARNING: Your proxy is only valid for ',str(timeLeft),' hours -> Renew it with:')
        print('voms-proxy-init -voms cms -rfc --valid 168:0')
        exit()

### Methods for analyzing shapes 

def getShapeDirName(shapeDir, year, tag, fitoption=''):

    shapeDirList = [ shapeDir, year, tag.split('_')[0], fitoption ]

    if fitoption!='':
        tag = tag.replace('___','_')
        if '__' in tag:
            shapeDirList.append(tag.replace(tag.split('__')[0],'').replace('__','/'))

    return '/'.join(shapeDirList)

def getShapeLocalFileName(tag, sigset, fileset='', fitoption=''):

    tag = tag.replace('___','_').split('__')[0]
    if fitoption=='': tag = tag.split('_')[0]
    return 'mkShapes__'+tag+getFilesetForShapesName(fileset, sigset)+'.root'

def getShapeFileName(shapeDir, year, tag, sigset, fileset='', fitoption=''):

    return getShapeDirName(shapeDir, year, tag, fitoption)+'/'+getShapeLocalFileName(tag, sigset, fileset)

def foundShapeFiles(opt, rawShapes=False, verbose=True):

    missingShapeFiles = False

    for year in opt.year.split('-'):
        for tag in opt.tag.split('-'):
            rawtag = tag.split('_')[0] if rawShapes else tag

            if not os.path.isfile(getShapeFileName(opt.shapedir, year, rawtag, opt.sigset, opt.fileset)): 
                if verbose: print('Error: input shape file', getShapeFileName(opt.shapedir, year, rawtag, opt.sigset, opt.fileset), 'is missing')
                missingShapeFiles = True
     
    return not missingShapeFiles

def getParentDir(path):

    return path.replace(path.split('/')[-1],'')

def openRootFile(fileName, mode='READ'):

    if mode=='recreate':
        os.system('mkdir -p '+getParentDir(fileName))

    return ROOT.TFile(fileName, mode)

def openShapeFile(shapeDir, year, tag, sigset, fileset='', mode='READ'):

    return openRootFile(getShapeFileName(shapeDir, year, tag, sigset, fileset), mode)

def mergeDataTakingPeriodShapes(opt, years, tag, fileset, strategy='deep', outputdir=None, inputnuisances=None, outputnuisances=None, verbose=False):

    mergeCommandList = [ '--inputDir='+opt.shapedir, '--years='+years, '--tag='+tag, '--sigset='+fileset, '--nuisancesFile='+inputnuisances ]
    if verbose: mergeCommandList.append('--verbose')

    if strategy=='deep': mergeCommandList.extend([ '--outputShapeDir='+outputdir, '--skipLNN' ])
    else:                mergeCommandList.extend([ '--outputNuisFile='+outputnuisances, '--saveNuisances' ])

    os.system('mergeDataTakingPeriodShapes.py '+' '.join( mergeCommandList ))

### Pre-fit tables

def yieldsTables(opt, masspoints=''):

    if 'fit' in opt.option.lower(): postFitYieldsTables(opt, masspoints)
    else: 
        print('please, complete me :(')
        print('using postFitYieldsTables for the time being')
        opt.option += 'prefit'
        postFitYieldsTables(opt, masspoints)

def systematicsTables(opt):

    print('please, port me from https://github.com/scodella/PlotsConfigurations/blob/worker/Configurations/SUS-19-XXX/mkSystematicsTables.py :(')

### Modules for analyzing results from combine

def setupCombineCommand(opt, joinstr=''):

    combineCommandList = [ 'cd '+opt.combineLocation, 'eval `scramv1 runtime -sh`', 'cd '+opt.baseDir ]
    if joinstr=='': return combineCommandList
    else: return joinstr.join(combineCommandList)

def getCombineOptionFlag(option, isForPlot=False):

    combineOptionFlag = '_Toy' if 'toy' in option.lower() else ''
    if 'asimovb' in option.lower(): combineOptionFlag = '_asimovB'
    if 'asimovs' in option.lower(): combineOptionFlag = '_asimovS'
    if 'asimovi' in option.lower(): combineOptionFlag = '_asimovI'
    if not isForPlot: return combineOptionFlag
    else:
        if combineOptionFlag=='': return 'FitsToData'
        else: return combineOptionFlag.replace('_a', 'A')

def getCombineOutputFileName(opt, signal, year='', tag='', combineAction=''):

    if year=='': year = opt.year
    if tag=='': tag = opt.tag
    if getCombineOptionFlag(opt.option) not in tag: tag += getCombineOptionFlag(opt.option)

    if hasattr(opt, 'combineAction'):
        combineAction = opt.combineAction

    if combineAction=='limits':
        combineOutDir = 'limitdir'
        if 'toy' in opt.option:
            outputFileName = 'higgsCombineTest.HybridNew.mH120.root'
        else:
            limitRun = 'Both' if opt.unblind else 'Blind'
            outputFileName = 'higgsCombine_'+limitRun+'.AsymptoticLimits.mH120.root'
    elif combineAction=='goffit':
        combineOutDir = 'gofitdir'
        outputFileName = 'goodnessOfFit'+getCombineOptionFlag(opt.option)+'.root'
    elif combineAction=='mlfits': 
        combineOutDir = 'mlfitdir'
        outputFileName = 'fitDiagnostics'+getCombineOptionFlag(opt.option)+'.root'
    elif combineAction=='impacts':
        combineOutDir = 'impactdir'
        outputFileName = 'impacts.pdf'
    elif 'impacts' in combineAction:
        combineOutDir = 'impactdir'
        outputFileName = combineAction
    else:
        print('Error in getCombineOutputFileName: please speficy if you want the output from a limit or a ML fit')
        exit()

    return getSignalDir(opt, year, tag, signal, combineOutDir)+'/'+outputFileName

def openCombineLimitFile(opt, signal, year='', tag=''):

    return openRootFile(getCombineLimitFileName(opt, signal, year, tag))

def getCombineLimitFileName(opt, signal, year='', tag=''):

    return getCombineOutputFileName(opt, signal, year, tag, 'limits')

def openCombineFitFile(opt, signal, year='', tag=''):

    return openRootFile(getCombineFitFileName(opt, signal, year, tag))

def getCombineFitFileName(opt, signal, year='', tag=''):

    return getCombineOutputFileName(opt, signal, year, tag, 'mlfits')

def goodCombineFit(opt, year, tag, signal, fitoption):

    fitFile = openRootFile(getCombineFitFileName(opt, signal, year, tag))
    if not fitFile.Get('shapes_'+fitoption.lower().replace('postfit','fit_')): return False
    return True

def deleteLimits(opt):

    opt.shapedir = opt.limitdir
    deleteShapes(opt)

def purgeLimits(opt):

    deleteDirectory(opt.limitdir+'/*')

def deleteMLFits(opt):

    opt.shapedir = opt.mlfitdir
    deleteShapes(opt)

def purgeMLFits(opt):

    deleteDirectory(opt.mlfitdir+'/*')

def massScanLimits(opt):

    print('please, port me from https://github.com/scodella/PlotsConfigurations/blob/worker/Configurations/SUS-19-XXX/analyzeLimits.py :(')

def fitMatrices(opt):

    signals = getSignalList(opt)
    yearList = opt.year.split('-') if 'split' in opt.option else [ opt.year ]    

    fitlevels = []
    if 'prefit' in opt.option.lower(): fitlevels.append('prefit')
    elif 'postfitb' in opt.option.lower(): fitlevels.append('fit_b')
    elif 'postfits' in opt.option.lower(): fitlevels.append('fit_s')
    else: print('Error in fitMatrices: please choose a fit level (prefit, postfitb, postfits)')

    for year in yearList:
        for tag in opt.tag.split('-'):
            for fitlevel in fitlevels:

                optAux = copy.deepcopy(opt)
                optAux.year, optAux.tag = year, year+tag
                signals = getSignalList(optAux)
                luminosity = int(round(opt.lumi, 0)) if opt.lumi>100 else round(opt.lumi, 1)
                legend = '\'L = '+str(luminosity)+'/fb (#sqrt{s} = 13 TeV)\''
                fitoption = fitlevel.replace('prefit','PreFit').replace('fit_b','PostFitB').replace('fit_s','PostFitS')
                mainOutputDir = '/'.join([ opt.plotsdir, year, tag, getCombineOptionFlag(opt.option,True) ])        

                commandList = [ '--postFit='+fitlevel, '--legend='+legend ]
                if 'nosavecov' not in opt.option.lower(): commandList.append('--saveCovariance')
                if 'cutsToRemove:' in opt.option:
                    commandList.append('--cutsToRemove='+opt.option.split('cutsToRemove:')[1].split(':')[0])
                if 'nuisToRemove:' in opt.option:
                    commandList.append('--nuisToRemove='+opt.option.split('nuisToRemove:')[1].split(':')[0])
 
                for signal in signals:

                    signalCommandList = commandList
                    signalCommandList.append('--inputFile='+getCombineFitFileName(opt, signal, year, tag))
                    signalCommandList.append('--outputDir='+'/'.join([ mainOutputDir, fitoption, signal, 'FitMatrices' ]))
                    signalCommandList.append('--signal='+signal)

                    if not 'onlynuis' in opt.option.lower(): os.system('mkMatrixPlots.py '+' '.join(signalCommandList))
                    if not 'onlycuts' in opt.option.lower(): os.system('mkMatrixPlots.py '+' '.join(signalCommandList+['--doNuisances']))
                    copyIndexForPlots('/'.join([ mainOutputDir, fitoption, signal, 'FitMatrices' ]))

def postFitYieldsTables(opt, cardNameStructure='cut', masspoints=''):

    yearList = opt.year.split('-') if 'split' in opt.option else [ opt.year ]

    if 'prefit' in opt.option.lower(): fittype = 'PreFit'
    elif 'postfitb' in opt.option.lower(): fittype = 'PostFitB'
    else: fittype = 'PostFitS'

    for year in yearList:
        for tag in opt.tag.split('-'):

            commandList = [ '--tag='+tag, '--year='+year, '--fit='+fittype, '--cardName='+cardNameStructure, '--masspoints='+masspoints ]
            commandList.append('--outputTableDir='+'/'.join([ opt.tabledir, year, tag ]))
            
            if 'fromshapes' in opt.option:
                commandList.append('--fromshapes')
                if 'merged' in opt.option: commandList.append('--mergedyears')
                dataflag = 'AsimovB' if 'asimovb' in opt.option else 'AsimovS' if 'asimovs' in opt.option else 'FitsToData'
                yearFlag = year if len(yearList)>1 else ''
                commandList.append('--inputDir='+'/'.join([ opt.shapedir, year, tag.split('_')[0], dataflag, fittype+yearFlag ]))
            else:
                dataflag = '_asimovB' if 'asimovb' in opt.option else '_asimovS' if 'asimovs' in opt.option else ''
                commandList.append('--inputDirMaxFit='+'/'.join([ opt.mlfitdir, year, tag+dataflag ]))

            if opt.unblind: commandList.append('--unblind')
            if 'nosignal' in opt.option: commandList.append('--nosignal')

            os.system('mkPostFitYieldsTables.py '+' '.join(commandList))

def loadImpactsJSON(opt, year = '', tag = '', signal = '', jsonName = 'impacts.json'):

    if signal=='': signal = opt.sigset
    if year=='': year = opt.year
    if tag=='': tag = opt.tag
    return loadJSON(getCombineOutputFileName(opt, signal, year, tag, jsonName))

def loadImpactsParams(opt, year = '', tag = '', signal = '', jsonName = 'impacts.json'):

    impactsJSON = loadImpactsJSON(opt, year, tag, signal, jsonName)
    return impactsJSON['params']

def loadRateParamsFromImpacts(opt, year = '', tag = '', signal = '', jsonName = 'impacts.json'):

    rateParams = {}

    impactsParams = loadImpactsParams(opt, year, tag, signal, jsonName)
    for param in range(len(impactsParams)):
        if impactsParams[param]['type']=='Unconstrained':
            rateParams[impactsParams[param]['name']] = {}
            for key in [ 'fit', 'groups', 'impact_r', 'prefit', 'r' ]:
                rateParams[impactsParams[param]['name']][key] = impactsParams[param][key]

    return rateParams

def loadFitParams(opt, year = '', tag = '', signal = '', fitoption = 'b'):

    fitParams = {}

    if signal=='': signal = opt.sigset
    if year=='': year = opt.year
    if tag=='': tag = opt.tag
    fitRootFile = openCombineFitFile(opt, signal, year, tag)
    fitResults = fitRootFile.Get('fit_'+fitoption).floatParsFinal()
    for param in range(fitResults.getSize()):
        nuis = fitResults.at(param)
        fitParams[nuis.GetName()] = {}
        fitParams[nuis.GetName()]['value'] = nuis.getVal()
        fitParams[nuis.GetName()]['error'] = nuis.getError()
        fitParams[nuis.GetName()]['errorHi'] = nuis.getErrorHi()
        fitParams[nuis.GetName()]['errorLo'] = nuis.getErrorLo()

    return fitParams

### Methods for computing weights, efficiencies, scale factors, etc.

def getPileupScenarioFromSimulation(opt):

    if 'pu:' not in opt.option:
        print('Please, specify the pileup variable name')
        exit()

    pileupVariable = opt.option.split('pu:')[-1].split(':')[0]

    outputDir = '/'.join([ opt.datadir, opt.year, 'Pileup', '' ])
    os.system('mkdir -p '+outputDir)

    samples = getSamples(opt)

    for sample in samples:
        if not samples[sample]['isDATA']:
            if sample in opt.option:

                events = ROOT.TChain(opt.treeName)
                for tree in samples[sample]['name']: events.Add(tree.replace('#','')) 

                pileup = bookHistogram('pileup', [ 100, 0, 100 ])
                events.Draw(pileupVariable+'>>pileup')

                outputRoot = openRootFile(outputDir+'pileup_'+sample+'.root','recreate')
                pileup.Write('pileup')
                outputRoot.Close()
    
def writePileupScenarioFromList(opt):

    if not hasattr(opt, 'simulationPileupList'):
        print('Missing simulation pileup list')
        exit()

    outputDir = '/'.join([ opt.datadir, opt.year, 'Pileup', '' ])
    os.system('mkdir -p '+outputDir)

    nBins = len(opt.simulationPileupList)
    pileup = bookHistogram('pileup', [ nBins, 0, nBins ])
    for ibin in range(nBins):
        pileup.SetBinContent(ibin+1, opt.simulationPileupList[ibin])


    outputRoot = openRootFile(outputDir+opt.simulationPileupFile,'recreate')
    pileup.Write('pileup')
    outputRoot.Close()

def pileupWeights(opt, dataFile = '', simulationFile = '', outputFile = ''):
 
    if 'dataFile:' in opt.option: 
        dataFile = opt.option.split('dataFile:')[-1].split(':')[0]
    elif dataFile=='':
        if hasattr(opt, 'dataPileupFile'):
            dataFile = opt.dataPileupFile
        else:
            print('Missing data input file')
            exit()

    profileDir = '/'.join([ os.getenv('PWD'), '../../../LatinoAnalysis/NanoGardener/python/data/PUweights', opt.year, '' ])
    outputDir = '/'.join([ opt.datadir, opt.year, 'Pileup/' ])

    if 'simulationFile:' in opt.option:
        simulationFile = opt.option.split('simulationFile:')[-1].split(':')[0]
    elif simulationFile=='':
        if hasattr(opt, 'simulationPileupFile'):
            simulationFile = opt.simulationPileupFile
            if not isGoodFile(outputDir+simulationFile, 0.):
                print('Simulation input file does not exist')
                if hasattr(opt, 'simulationPileupList'):
                    print('Writing simulation input file from list')
                    writePileupScenarioFromList(opt)
                else:
                    exit()
        else:
            print('Missing simulation input file')
            exit()

    if '/' not in dataFile: dataFile = profileDir+dataFile
    if '/' not in simulationFile: simulationFile = outputDir+simulationFile

    dataFile = dataFile.replace('.root','')
    simulationFile = simulationFile.replace('.root','')

    if 'outputFile:' in opt.option:
        outputFile = opt.option.split('outputFile:')[-1].split(':')[0].replace('.root','')
    elif outputFile=='':
        if hasattr(opt, 'pileupWeightsFile'):
            outputFile = opt.pileupWeightsFile
        else:
            os.system('mkdir -p '+outputDir)
            outputFile = outputDir+'pileupWeights_'+dataFile.split('/')[-1]
           
    dataRoot = openRootFile(dataFile+'.root')
    simulationRoot = openRootFile(simulationFile+'.root')   
     
    if 'onlyplot' not in opt.option:
        outputRoot = openRootFile(outputFile+'.root','recreate')

    simulationPileup = simulationRoot.Get('pileup')
    simulationPileup.Scale(1./simulationPileup.Integral())

    if 'plot' in opt.option:
        canvas = bookCanvas('canvas',600,400)
        copyIndexForPlots('/'.join([ opt.plotsdir, opt.year, 'Pileup' ]))
        if 'plotFile:' in opt.option:
            plotFile = opt.option.split('plotFile:')[-1].split(':')[0].replace('.png','')
        else:
            plotFile = dataFile.split('/')[-1]
    else: plotFile = 'None'
       
    if opt.debug:
        print('dataFile:', dataFile, 'simulationFile:', simulationFile, 'plotFile:', plotFile, 'outputFile:', outputFile)
 
    for pileup in [ 'pileup', 'pileup_minus', 'pileup_plus' ]:

        dataPileup = dataRoot.Get(pileup)
        dataPileup.Scale(1./dataPileup.Integral())

        if dataPileup.GetNbinsX()!=simulationPileup.GetNbinsX():
            print('Error: data and simulation pileup histograms have different binning')
            exit()

        if pileup=='pileup' and 'plot' in opt.option:
            canvas.cd()
            dataPileup.SetLineColor(2)
            dataPileup.SetLineWidth(2)
            simulationPileup.SetLineWidth(2)
            dataPileup.SetXTitle('Pileup')
            dataPileup.SetYTitle('Event fraction / pileup')
            dataPileup.Draw('histo')
            simulationPileup.Draw('histosame')
            canvas.Print('/'.join([ opt.plotsdir, opt.year, 'Pileup', plotFile+'.png' ]))

        dataPileup.Divide(simulationPileup)

        if 'onlyplot' not in opt.option:
            outputRoot.cd()
            dataPileup.Write(pileup)
      
    if 'onlyplot' not in opt.option: outputRoot.Close()
    dataRoot.Close()
    simulationRoot.Close()

def triggerEfficiencies(opt):

    print('please, port me from https://github.com/scodella/PlotsConfigurations/blob/worker/Configurations/SUS-19-XXX/mkTriggerEfficiencies.py :(')

def theoryNormalizations(opt):

    print('please, port me from https://github.com/scodella/PlotsConfigurations/blob/worker/Configurations/SUS-19-XXX/computeTheoryNormalizations.py :(')

def backgroundScaleFactors(opt):

    print('please, port me fromhttps://github.com/scodella/PlotsConfigurations/blob/worker/Configurations/SUS-19-XXX/mkBackgroundScaleFactors.py :(')

