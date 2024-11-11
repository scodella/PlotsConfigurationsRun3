import os
import glob
import copy
import math
import PlotsConfigurations.Tools.commonTools as commonTools
from LatinoAnalysis.Tools.batchTools import *

### Shapes

def mkShapesMulti(opt, year, tag, splits, action):

    mainDir = '/'.join([ opt.shapedir, year, tag ])

    shapeScript = 'mkShapesMulti.py' if 'mkshape' not in opt.option.lower() else 'mkShapes.py'
    shapeMultiCommand = shapeScript+' --pycfg='+opt.configuration+' --treeName='+opt.treeName+' --tag='+year+tag+' --sigset=SIGSET'
    if 'shapes' in action:
        if not opt.interactive: shapeMultiCommand += ' --doBatch=True --batchQueue='+opt.batchQueue
        if opt.dryRun: shapeMultiCommand += ' --dry-run '
    else:
        shapeMultiCommand += ' --doHadd=True --doNotCleanup'

    for split in splits:
        if len(splits[split])>0:

            splitDir = mainDir + '/' + split
            os.system('mkdir -p '+splitDir)

            splitCommand = shapeMultiCommand+' --outputDir='+splitDir+' --batchSplit='+split
 
            if 'merge' in action:

                sampleFlag = '_SIGSET' if 'mkshape' not in opt.option.lower() else '' #if 'worker' in commonTools.getBranch() else '' 
                outputDir = mainDir if 'mergeall' in action else mainDir+'/Samples'
                splitCommand += ' ; mkdir -p '+outputDir+' ; mv '+splitDir+'/plots_'+year+tag+sampleFlag+'.root '+outputDir
                if 'mergesingle' in action: splitCommand += '/plots_'+year+tag+'_ALL_SAMPLE.root'
                else: splitCommand += '/plots_'+tag+commonTools.setFileset('',opt.sigset)+'.root'
          
            for sample in splits[split]:
                commonTools.resetShapes(opt, split, year, tag, sample, opt.reset)
                os.system(splitCommand.replace('SIGSET', sample).replace('SAMPLE', sample.split(':')[-1]))
 
def getSplits(opt, year, tag, action):

    splits = { 'Samples' : [ ], 'AsMuchAsPossible' : [ ] }

    samples = commonTools.getSamplesInLoop(opt.configuration, year, tag, opt.sigset)

    for sample in samples:
        treeType = samples[sample]['treeType']+':'
        if 'split' in samples[sample] and samples[sample]['split']=='AsMuchAsPossible':
            if opt.recover:
                jobsForSamples = 0
                if 'FilesPerJob' in samples[sample]: jobsForSamples = int(math.ceil(float(len(samples[sample]['name']))/samples[sample]['FilesPerJob']))
                elif 'JobsPerSample' in samples[sample]: jobsForSamples = int(samples[sample]['JobsPerSample']) 
                if jobsForSamples>0:
                    if commonTools.countedSampleShapeFiles(opt.shapedir, year, tag, sample)==jobsForSamples: continue
            if 'FilesPerJob' not in samples[sample]:
                if 'JobsPerSample' not in samples[sample]:
                    print('Warning:', sample, 'has neither FilesPerJob nor JobsPerSample options')
                    continue
                ntrees, multFactor = len(samples[sample]['name']), int(samples[sample]['JobsPerSample'])
                samples[sample]['FilesPerJob'] = int(math.ceil(float(ntrees)/multFactor))
            splits['AsMuchAsPossible'].append(treeType+sample)
        elif 'shapes' in action:
            if opt.recover and commonTools.foundSampleShapeFile(opt.shapedir, year, tag, sample): continue
            if 'split' in samples[sample] and samples[sample]['split']=='Single':
                splits['Samples'].append(treeType+':'+sample)
            else: 
                sampleList = -1
                for ilist in range(len(splits['Samples'])):
                    if treeType in splits['Samples'][ilist] and '::' not in splits['Samples'][ilist]:
                        sampleList = ilist
                if sampleList==-1: splits['Samples'].append(treeType+sample)
                else:              splits['Samples'][sampleList] += ','+sample
                
    return splits

def shapes(opt):

    if '_' in opt.tag:
        print('Error in shapes: one of the selecteg tags contains an \'_\'.') 
        print('                 Please use \'_\' only to set datacard options.')
        exit()

    if not opt.interactive: opt.batchQueue = commonTools.batchQueue(opt, opt.batchQueue)

    commonTools.cleanLogs(opt)

    for year in opt.year.split('-'):
        for tag in opt.tag.split('-'):
            splits = getSplits(opt, year, tag, 'shapes')
            mkShapesMulti(opt, year, tag, splits, 'shapes')

def mergesingle(opt):

    for year in opt.year.split('-'):
        for tag in opt.tag.split('-'):
            splits = getSplits(opt, year, tag, 'mergesingle')
            mkShapesMulti(opt, year, tag, splits, 'mergesingle')

def mergeall(opt):

    splits = { 'Samples' : [ opt.sigset ] }

    for year in opt.year.split('-'):
        for tag in opt.tag.split('-'):
            mkShapesMulti(opt, year, tag, splits, 'mergeall')

def remakeMissingShapes(opt, method='resubmit'):

    sampleShapeDir = '/'.join([ opt.shapedir, opt.year, opt.tag, 'AsMuchAsPossible' ])

    for shFile in commonTools.getLogFileList(opt, 'sh'):

        sample = shFile.split('/')[3]
        if not commonTools.isGoodFile(sampleShapeDir+'/plots_'+opt.year+opt.tag+'_ALL_'+sample+'.root', 0):

            missingShape = False
            if 'force' in opt.option.lower(): missingShape = True
            if commonTools.isGoodFile(shFile.replace('.sh','.done'), 0): missingShape = True
            if commonTools.isGoodFile(shFile.replace('.sh','.err'), 0) and commonTools.hasString(shFile.replace('.sh','.err'), 'RuntimeError'): missingShape = True
            if commonTools.isGoodFile(shFile.replace('.sh','.err'), 0) and commonTools.hasString(shFile.replace('.sh','.err'), 'ImportError'): missingShape = True
            if commonTools.isGoodFile(shFile.replace('.sh','.err'), 0) and commonTools.hasString(shFile.replace('.sh','.err'), 'OSError'): missingShape = True
            if commonTools.isGoodFile(shFile.replace('.sh','.err'), 0) and commonTools.hasString(shFile.replace('.sh','.err'), 'TypeError:'): missingShape = True
            if commonTools.isGoodFile(shFile.replace('.sh','.err'), 0) and commonTools.hasString(shFile.replace('.sh','.err'), 'Segmentation fault'): missingShape = True
            if commonTools.isGoodFile(shFile.replace('.sh','.err'), 0) and commonTools.hasString(shFile.replace('.sh','.err'), 'logic_error'): missingShape = True 
            if commonTools.isGoodFile(shFile.replace('.sh','.err'), 0) and commonTools.hasString(shFile.replace('.sh','.err'), 'AttributeError'): missingShape = True
            if commonTools.isGoodFile(shFile.replace('.sh','.err'), 0) and commonTools.hasString(shFile.replace('.sh','.err'), '(core dumped)'): missingShape = True
            if commonTools.isGoodFile(shFile.replace('.sh','.err'), 0) and commonTools.hasString(shFile.replace('.sh','.err'), '*** Break *** bus error'): missingShape = True
            if commonTools.isGoodFile(shFile.replace('.sh','.err'), 0) and commonTools.hasString(shFile.replace('.sh','.err'), '*** Break *** segmentation violation'): missingShape = True
            if commonTools.isGoodFile(shFile.replace('.sh','.err'), 0) and commonTools.hasString(shFile.replace('.sh','.err'), 'Input/output error'): missingShape = True
            if commonTools.isGoodFile(shFile.replace('.sh','.err'), 0) and commonTools.hasString(shFile.replace('.sh','.err'), 'error reading from file'): missingShape = True
            if commonTools.isGoodFile(shFile.replace('.sh','.err'), 0) and commonTools.hasString(shFile.replace('.sh','.err'), 'doesn\'t exist'): missingShape = True
            if commonTools.isGoodFile(shFile.replace('.sh','.log'), 0) and commonTools.hasString(shFile.replace('.sh','.log'), 'EXCEED'): missingShape = True
            if not commonTools.isGoodFile(shFile.replace('.sh','.jid'), 0) and not commonTools.isGoodFile(shFile.replace('.sh','.done'), 0): missingShape = True

            if missingShape:

                if method=='resubmit':
                    for extensionToRemove in [ '.err', '.log', '.out', '.done', '.jid' ]:
                        if commonTools.isGoodFile(shFile.replace('.sh',extensionToRemove), 0): os.system('rm '+shFile.replace('.sh',extensionToRemove))
                    makeShapeCommand = 'condor_submit '+shFile.replace('.sh','.jds')+' > ' +shFile.replace('.sh','.jid')

                elif method=='recover':
                    makeShapeCommand = ' ; '.join([ 'cd '+commonTools.getLogDir(opt, opt.year, opt.tag)+'/'+sample+'/', './'+shFile.split('/')[-1], 'cd - ' ])

                print('  Remaking missing shape for', opt.year, opt.tag, sample)
                if opt.dryRun: print(makeShapeCommand)
                else: os.system(makeShapeCommand)
            
            elif commonTools.isGoodFile(shFile.replace('.sh','.err'), 0): print('  Job with error to check:', opt.year, opt.tag, sample)

        else:
            os.system('rm -r '+shFile.replace(shFile.split('/')[-1],''))

### Plots

def mkPlot(opt, year, tag, sigset, nuisances, fitoption='', yearInFit='', extraOutDirFlag=''):

    plotAsExotics = commonTools.plotAsExotics(opt)

    plotsDirList = [ opt.plotsdir, year ]

    if fitoption=='':
        fileset = opt.fileset
        sample = '' if (sigset=='SM' or sigset=='') else sigset.split(':')[-1]+extraOutDirFlag
        plotsDirList.extend([ tag.split('___')[0].replace('__','/'), sample ])
        lumiYear = year

    else:
        fileset = ''
        if yearInFit==year: yearInFit = ''
        lumiYear = yearInFit if yearInFit!='' else year
        signal = '' 
        if sigset!='SM' and sigset!='':
            signal = sigset
            for ismp in range(len(sigset.split('_')[0].split('-'))-1):
                signal = signal.replace(sigset.split('_')[0].split('-')[ismp]+'-','')
        plotsDirList.extend([ tag.split('___')[0].replace('__','/'), fitoption, signal, yearInFit ])
        if 'PostFitS' in fitoption: plotAsExotics = False

    plotsDir = '/'.join(plotsDirList)

    shapeFileName = commonTools.getShapeFileName(opt.shapedir, year, tag, sigset, fileset, fitoption+yearInFit) 

    os.system('mkdir -p '+plotsDir+' ; cp ../../index.php '+opt.plotsdir)
    commonTools.copyIndexForPlots(opt.plotsdir, plotsDir)

    plotCommand = 'mkPlot.py --pycfg='+opt.configuration+' --tag='+lumiYear+tag+' --sigset='+sigset+' --inputFile='+shapeFileName+' --outputDirPlots='+plotsDir+' --maxLogCratio=1000 --minLogCratio=0.1 --maxLogC=1000  --scaleToPlot=2 --nuisancesFile='+nuisances+' --fileFormats=\'png,root\''

    if 'normalizedCR' in opt.option: plotCommand += ' --plotNormalizedCRratio=1' # This is not yet re-implemented in latino's mkPlot.py
    elif 'normalized' in opt.option: plotCommand += ' --plotNormalizedDistributions --plotNormalizedIncludeData'
    if plotAsExotics:                plotCommand += ' --showDataVsBkgOnly'       # This is not yet re-implemented in latino's mkPlot.py
    if 'noyields' not in opt.option: plotCommand += ' --showIntegralLegend=1'
    if 'saveC'        in opt.option: plotCommand  = plotCommand.replace('--fileFormats=\'','--fileFormats=\'C,')
    if 'savePDF'      in opt.option: plotCommand  = plotCommand.replace('--fileFormats=\'','--fileFormats=\'pdf,')
    if 'plotsmearvar' in opt.option: plotCommand += ' --plotSmearVariation=1'    # This is not yet re-implemented in latino's mkPlot.py
    if 'postfit' in opt.option.lower(): plotCommand += ' --postFit=p'
    if 'nostat' in opt.option.lower() : plotCommand += ' --removeMCStat'
    if 'nuisanceVariations' in opt.option: plotCommand += ' --nuisanceVariations'
    if 'onebin' in opt.option.lower() : plotCommand += ' --mergeBins'
    if 'cutlabel' in opt.option.lower(): plotCommand += ' --addCutLabels'
    if opt.paperStyle: plotCommand += ' --paperStyle'

    os.system(plotCommand)

    if not opt.keepallplots:
        plotToDelete = 'c_' if ('SM' in opt.sigset or 'keepratioplots' in opt.option) else 'cratio_'
        for plot2delete in [ plotToDelete, 'log_'+plotToDelete, 'cdifference_', 'log_cdifference_' ]:
            os.system('rm '+plotsDir+'/'+plot2delete+'*')

# Plot shape nuisances

def plotNuisances(opt):

   opt.fileset = commonTools.setFileset(opt.fileset, opt.sigset)
   opt.samplesFile = commonTools.getCfgFileName(opt, 'samples')
   opt.option += 'keepratioplots'

   yearList = opt.year.split('-') if 'merge' not in opt.option else [ opt.year ]

   for year in yearList:
       for tag in opt.tag.split('-'):

           opt2 = copy.deepcopy(opt)
           opt2.year, opt2.tag = year, tag
     
           singleNuisances = {}

           if year.split('-')>1:

               outputNuisances =  '_'.join([ 'nuisances', year, tag, opt.sigset+'.py' ])
               commonTools.mergeDataTakingPeriodShapes(opt, year, tag, opt.fileset[1:], '', 'None', commonTools.getCfgFileName(opt, 'nuisances'), outputNuisances, opt.verbose)

               samples, cuts, variables = commonTools.getDictionaries(opt2, 'variables')
               nuisances = {}
               handle = open(outputNuisances,'r')
               exec(handle)
               handle.close()
               os.system('rm -f '+outputNuisances)

           else:

               samples, cuts, variables, nuisances = commonTools.getDictionaries(opt2)

           for nuisance in nuisances:
               if nuisance=='stat' or ('type' in nuisances[nuisance] and nuisances[nuisance]['type']=='shape'):
                   singleNuisanceName = 'statistics' if nuisance=='stat' else nuisances[nuisance]['name']
                   if 'nuisances:' not in opt.option or singleNuisanceName in opt.option:
                       nuisanceName = 'statistics' if nuisance=='stat' else nuisance
                       if singleNuisanceName not in singleNuisances:
                           singleNuisances[singleNuisanceName] = { }
                       singleNuisances[singleNuisanceName][nuisanceName] = nuisances[nuisance]

           for singleNuisance in singleNuisances:

               opt2.option = opt.option if singleNuisance=='statistics' else opt.option+'nuisanceVariations'

               backgroundList, sampleList = [], []

               for sample in samples:
                   useThisSample = singleNuisance=='statistics'
                   if not useThisSample:
                       for nuisanceName in singleNuisances[singleNuisance]:
                           if sample in nuisances[nuisanceName]['samples']:
                               useThisSample = True
                               break
                   if useThisSample:
                       if samples[sample]['isSignal']: sampleList.append(sample)
                       elif sample not in backgroundList: 
                           backgroundTreeType = samples[sample]['treeType']
                           backgroundList.append(sample)

               if len(backgroundList)>=1:
                   sampleList.append(backgroundTreeType)
                   if len(backgroundList)<=3: 
                       sampleList.append(backgroundTreeType+':'+','.join(backgroundList))                        
 
               singleNuisanceFile = './nuisance_'+singleNuisance+'_'+opt.year+opt.tag+'.py'
               with open(singleNuisanceFile, 'w') as file:
                   file.write('nuisances = '+str(singleNuisances[singleNuisance]))                   

               for samplesToPlot in sampleList:
                   opt2.sigset = samplesToPlot
                   mkPlot(opt2, year, tag, opt2.sigset, singleNuisanceFile, extraOutDirFlag='_'+singleNuisance)

               os.system('rm '+singleNuisanceFile)

# Plots merging different data taking periods (years) without combine (e.g. control regions)

def mergedPlots(opt):

    inputNuisances = commonTools.getCfgFileName(opt, 'nuisances') if 'nonuisance' not in opt.option else 'None'
    fileset = commonTools.setFileset(opt.fileset, opt.sigset)
    if fileset[0]=='_': fileset = fileset[1:]

    for tag in opt.tag.split('-'):

        if opt.deepMerge!=None:
            year = opt.deepMerge
            outputNuisances = inputNuisances
            outputDir = '/'.join([ opt.shapedir, year, tag ])
            commonTools.mergeDataTakingPeriodShapes(opt, opt.year, tag, fileset, 'deep', outputDir, inputNuisances, 'None', opt.verbose)

        else:
            year = opt.year
            outputNuisances =  '_'.join([ 'nuisances', opt.year, opt.tag, opt.sigset+'.py' ])
            commonTools.mergeDataTakingPeriodShapes(opt, opt.year, tag, fileset, '', 'None', inputNuisances, outputNuisances, opt.verbose)
        
        mkPlot(opt, year, tag, opt.sigset, outputNuisances)
        os.system('rm -f nuisances_*.py')

# Tools for making plots from combine fits

def getDatacardNameStructure(addYearToDatacardName, addCutToDatacardName, addVariableToDatacardName):

    datacardNameStructureList = [ ]
    if addCutToDatacardName: datacardNameStructureList.append('cut')
    if addVariableToDatacardName: datacardNameStructureList.append('variable')
    if addYearToDatacardName: datacardNameStructureList.append('year')
    return '_'.join(datacardNameStructureList)

def mkPostFitPlot(opt, fitoption, fittedYear, year, tag, cut, variable, signal, sigset, datacardNameStructure):

    fitkind = 'p' if 'PreFit' in fitoption else fitoption.split('PostFit')[-1].lower()
    postFitPlotCommandList = [ '--kind='+fitkind, '--structureFile='+commonTools.getCfgFileName(opt, 'structure') ]
    postFitPlotCommandList.extend([ '--tag='+fittedYear+tag, '--sigset='+sigset ])

    postFitPlotCommandList.extend([ '--cutNameInOriginal='+cut, '--variable='+variable ])
    postFitPlotCommandList.append('--cut='+datacardNameStructure.replace('year', year).replace('cut', cut).replace('variable', variable))
    if 'PostFitB' in fitoption: postFitPlotCommandList.append('--getSignalFromPrefit=1')

    tagoption = fitoption if year==fittedYear else fitoption+year
    postFitPlotCommandList.append('--inputFileCombine='+commonTools.getCombineFitFileName(opt, signal, fittedYear, tag))
    postFitPlotCommandList.append('--inputFile='+commonTools.getShapeFileName(opt.shapedir, year, tag.split('_')[0], opt.sigset, opt.fileset))
    postFitPlotCommandList.append('--outputFile='+commonTools.getShapeFileName(opt.shapedir, fittedYear, tag, sigset, '', tagoption))
    if 'asimov' in opt.option.lower(): postFitPlotCommandList.append('--getDataFromCombine')
    postFitPlotCommandList.append('--getDataFromCombine') # Check this

    os.system('mkPostFitPlot.py '+' '.join(postFitPlotCommandList))

def mergePostFitShapes(opt, postFitShapeFile, signal, mlfitDir, cardsDir, year, cut, variable, datacardNameStructure):

    combinedataset = '_asimovS' if 'asimovs' in opt.option.lower() else '_asimovB' if 'asimovb' in opt.option.lower() else ''
    fitdirectory = 'fit_b' if 'postfitb' in opt.option.lower() else 'fit_s'
    postfitoption = '--postfit' if 'postfit' in opt.option.lower() else ''
    kind = 'P' if 'postfit' in opt.option.lower() else 'p'

    commandList = [ ]

    if not os.path.exists(cardsDir): 
        opt.cardsdir = cardsDir
        datacards(opt, signal)

    outputCut = datacardNameStructure.replace('year',year).replace('cut',cut).replace('variable',variable).replace('*','').replace('__','_')
    if outputCut[0]=='_': outputCut = outputCut[1:]
    if outputCut[-1]=='_': outputCut = outputCut[:-1]

    inputCardList = []
    for card in glob.glob('/'.join([ cardsDir, year, opt.tag, signal, cut, variable, 'datacard.txt' ])):
        cardInputs = card.split(cardsDir)[1].split('/')
        inputCardName = datacardNameStructure.replace('year',cardInputs[1]).replace('cut',cardInputs[4]).replace('variable',cardInputs[5]) 
        inputCardList.append(inputCardName+'='+card.split(cardsDir+'/')[1])

    commandList = [ commonTools.setupCombineCommand(opt) ]
    commandList.append('cd '+cardsDir)
    commandList.append('combineCards.py '+' '.join(inputCardList)+' > combinedDatacard__'+outputCut+'.txt')
    commandList.append('text2workspace.py combinedDatacard__'+outputCut+'.txt')
    commandList.append('PostFitShapesFromWorkspace -w combinedDatacard__'+outputCut+'.root -o '+outputCut+'.root -d combinedDatacard__'+outputCut+'.txt -f '+mlfitDir+'/fitDiagnostics'+combinedataset+'.root:'+fitdirectory+' '+postfitoption+' --sampling --total-shapes')    
    commandList.append('cd '+opt.baseDir+'; eval `scramv1 runtime -sh`; cd -')
    commandList.append('mkPostFitCombinedPlot.py --inputFilePostFitShapesFromWorkspace='+outputCut+'.root --update --outputFile='+postFitShapeFile+' --signal='+signal+' --kind='+kind+' --cutName='+cut+' --variable='+variable+' --inputForData='+mlfitDir+'/fitDiagnostics'+combinedataset+'.root')

    os.system(' \n '.join(commandList))

def postFitPlots(opt, makePlots=True):

    fitoption = ''
    if 'prefit' in opt.option.lower(): fitoption = 'PreFit'
    elif 'postfitb' in opt.option.lower(): fitoption = 'PostFitB'
    elif 'postfits' in opt.option.lower(): fitoption = 'PostFitS'

    if fitoption=='':
        print('plotsPostFit error: please choose a fit option (prefit, postfitb, postfits)')
        exit()

    fittedYearList = opt.year.split('-') if 'split' in opt.option else [ opt.year ]
    if 'splitandcomb' in opt.option: fittedYearList.append(opt.year)

    for inputtag in opt.tag.split('-'):

        tag = inputtag
        if '_asimov' in inputtag:
           if 'asimov' not in opt.option:
               for tagsplit in inputtag.split('_'):
                   if 'asimov' in tagsplit: opt.option += tagsplit.lower()
           tag = tag.replace(commonTools.getCombineOptionFlag(opt.option), '')    
        combinetag = tag+commonTools.getCombineOptionFlag(opt.option)
        combinedataset = commonTools.getCombineOptionFlag(opt.option,True)
 
        for fittedYear in fittedYearList:

            yearInFitList = fittedYear.split('-')
            if 'mergeyear' in opt.option and '-' in fittedYear: yearInFitList.append(fittedYear) 

            signals = commonTools.getDictionariesInLoop(opt.configuration, yearInFitList[0], tag, opt.sigset, 'samples')
            for signal in signals:
                if signals[signal]['isSignal']:

                    if not commonTools.goodCombineFit(opt, fittedYear, combinetag, signal, fitoption):
                        print('Warning in postFitPlots: no good fit for year='+fittedYear+', tag='+tag+', signal='+signal+', fitoption='+fitoption)

                    sigset = opt.sigset if opt.sigset=='' or opt.sigset=='SM' else 'SM-'+signal if 'SM' in opt.sigset else signal

                    for year in yearInFitList:
                        if 'singleyear' in opt.option and 'singleyear'+str(year) not in opt.option: continue
                        if 'mergeyearonly' in opt.option and year!=fittedYear: continue

                        fityearoption = combinedataset+'/'+fitoption if year==fittedYear else combinedataset+'/'+fitoption+year
                        postFitShapeFile = commonTools.getShapeFileName(opt.shapedir, fittedYear, tag, sigset, '', fityearoption)    

                        if not opt.recover or not os.path.isfile(postFitShapeFile):
 
                            os.system('rm -f '+postFitShapeFile)
                            os.system('mkdir -p '+commonTools.getShapeDirName(opt.shapedir, fittedYear, tag, fityearoption))

                            samples, cuts, variables = commonTools.getDictionariesInLoop(opt.configuration, year, tag, sigset, 'variables', 'X')
                            datacardNameStructure = getDatacardNameStructure(len(fittedYear.split('-'))>1, len(list(cuts.keys()))>1, len(list(variables.keys()))>1)

                            if len(yearInFitList)>1 and year==fittedYear:
                                mlfitDir = commonTools.mergeDirPaths(os.getenv('PWD'), commonTools.getSignalDir(opt, opt.year, combinetag, signal, 'mlfitdir'))
                                cardsDir = mlfitDir+'/Datacards'
                                os.system('rm -r -f '+cardsDir)

                            for cut in cuts:
                                for variable in variables:
                                    if 'cuts' not in variables[variable] or cut in  variables[variable]['cuts']:

                                        if len(yearInFitList)==1 or year!=fittedYear:
                                            mkPostFitPlot(opt, combinedataset+'/'+fitoption, fittedYear, year, tag, cut, variable, signal, sigset, datacardNameStructure)

                                        elif cut not in samples[signal]['removeFromCuts']: # Check this
                                            opt2 = copy.deepcopy(opt)
                                            opt2.year, opt2.tag, opt2.sigset, opt2.baseDir = year, combinetag, sigset, os.getenv('PWD')
                                            postFitShapeFileFullPath = commonTools.mergeDirPaths(opt2.baseDir, postFitShapeFile)
                                            mergePostFitShapes(opt2, postFitShapeFileFullPath, signal, mlfitDir, cardsDir, '*', cut, variable, datacardNameStructure)

                            if len(yearInFitList)>1 and year==fittedYear: os.system('rm -r -f '+cardsDir)

                        if makePlots:
                            mkPlot(opt, fittedYear, tag, sigset, 'None', combinedataset+'/'+fitoption, year)

def postFitShapes(opt):

    postFitPlots(opt, False) 

# Generic plots from mkShapes output

def plots(opt):

    if 'prefit' in opt.option.lower() or 'postfit' in opt.option.lower(): postFitPlots(opt)
    elif 'merge' in opt.option: mergedPlots(opt)
    else: 

        if not commonTools.foundShapeFiles(opt, True): exit()

        nuisances = commonTools.getCfgFileName(opt, 'nuisances') if 'nonuisance' not in opt.option else 'None'

        for year in opt.year.split('-'):
            for tag in opt.tag.split('-'):
                mkPlot(opt, year, tag, opt.sigset, nuisances)

### Datacards

def getPerSignalSigset(inputfileset, inputsigset):

    fileset = commonTools.setFileset(inputfileset, inputsigset)

    if '-' in fileset:                       # This is SUSY like
        auxfileset = fileset if fileset[0]!='_' else fileset[1:]
        auxfileset = auxfileset.split('_')[0]
        sigset = auxfileset.replace(auxfileset.split('-')[-1], '')+'MASSPOINT'
    elif inputsigset=='' or inputsigset=='SM': # This should work for SM searches
        sigset = inputsigset
    else:                                    # Guessing latinos' usage
        sigset = 'MASSPOINT'

    return fileset, sigset

def datacards(opt, signal='', dryRun=False):

    fileset, sigset = getPerSignalSigset(opt.fileset, opt.sigset)

    if signal!='': 
        signalList = [ signal ]
    else: 
        signalList = []
        samples = commonTools.getSamples(opt)
        for sample in samples:
            if samples[sample]['isSignal']:
                signalList.append(sample)

    datacardCommandList = []

    blindData = '' if opt.unblind else ' --blindData '

    for year in opt.year.split('-'):
        for tag in opt.tag.split('-'):

            outtag = commonTools.getTagForDatacards(tag, opt.sigset)

            for sample in signalList:

                outputDir = commonTools.getSignalDir(opt, year, outtag, sample, 'cardsdir')

                datacardCommand = 'mkdir -p '+outputDir+' \n mkDatacards.py --pycfg='+opt.configuration+' --tag='+year+tag+' --sigset='+sigset.replace('MASSPOINT',sample)+' --outputDirDatacard='+outputDir+' --inputFile='+commonTools.getShapeFileName(opt.shapedir, year, tag.split('_')[0], '', fileset)+blindData

                if dryRun: datacardCommandList.append(datacardCommand) 
                else: os.system(datacardCommand)

    if dryRun: return datacardCommandList

### Batch

def submitJobs(opt, jobName, jobTag, targetList, splitBatch, jobSplit, nThreads):

    opt.batchQueue = commonTools.batchQueue(opt, opt.batchQueue)

    jobs = batchJobs(jobName,jobTag,['ALL'],list(targetList.keys()),splitBatch,'',JOB_DIR_SPLIT_READY=jobSplit)
    jobs.nThreads = nThreads

    for signal in targetList:
        jobs.Add('ALL', signal, targetList[signal])

    if not opt.dryRun:
        jobs.Sub(opt.batchQueue,opt.IiheWallTime,True)

