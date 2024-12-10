import os
import glob
import copy
import math
import commonTools

### Shapes

def mkShapesRDF(opt, year, tag, action):

    mkShapesRDFCommandList = [ 'mkShapesRDF' ]
    mkShapesRDFCommandList.append('--configFile='+commonTools.compileConfigurations(opt, action, year, tag, configsFolder=opt.configsFolder+'/'+action))

    if action=='shapes':
        mkShapesRDFCommandList.append('--operationMode=0')
        if not opt.interactive: mkShapesRDFCommandList.extend([ '--doBatch=1', '--queue='+opt.batchQueue ])
        else: mkShapesRDFCommandList.append('--limitEvents=100')
        if opt.dryRun: mkShapesRDFCommandList.append('--dryRun=1')

    elif 'jobs' in action: 
        mkShapesRDFCommandList.append('--operationMode=1')
        if 'resubmitall' in action: mkShapesRDFCommandList.append('--resubmit=2')
        elif 'resubmit' in action: mkShapesRDFCommandList.append('--resubmit=1')

    elif action=='mergeshapes':
        mkShapesRDFCommandList.insert(0, 'rm -f '+commonTools.getShapeFileName(opt.shapedir, year, tag, '', '', 'Split')+';')
        mkShapesRDFCommandList.append('--operationMode=2')
        mkShapesRDFCommandList.append('; mv '+commonTools.getShapeFileName(opt.shapedir, year, tag, '', '', 'Split')+' '+commonTools.getShapeFileName(opt.shapedir, year, tag, opt.sigset, ''))

    os.system(' '.join(mkShapesRDFCommandList))

def shapes(opt):

    if '_' in opt.tag:
        print('Error in shapes: one of the selected tags contains an \'_\'.') 
        print('                 Please use \'_\' only to set datacard options.')
        exit()

    if not opt.interactive: opt.batchQueue = commonTools.batchQueue(opt, opt.batchQueue)

    action = 'shapes'
    if opt.merge: action = 'mergeshapes'
    elif opt.checkjobs: action = 'checkjobs'
    elif opt.recover: 
        if opt.force: action = 'resubmitalljobs'
        else: action = 'resubmitjobs'

    for year in opt.year.split('-'):
        for tag in opt.tag.split('-'):

            if action=='shapes':
                if opt.reset: commonTools.resetShapes(opt, year, tag)
                else: commonTools.cleanShapeLogs(opt, year, tag, opt.sigset)

            mkShapesRDF(opt, year, tag, action)

### Plots

def mkPlot(opt, year, tag, sigset, fitoption='', yearInFit='', extraOutDirFlag=''):

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

    plotsDir = '/'.join(plotsDirList)
    commonTools.copyIndexForPlots(plotsDir)

    plotCommandList = [ 'mkPlot' ]
    plotCommandList.extend([ '--maxLogCratio=1000', '--minLogCratio=0.1', '--maxLogC=1000',  '--scaleToPlot=2' ]) 

    if 'normalized' in opt.option: plotCommandList.extend(['--plotNormalizedDistributions', '--plotNormalizedIncludeDats'])
    if commonTools.plotAsExotics(opt): plotCommandList.append('--showDataVsBkgOnly') # TODO
    if 'noyields' not in opt.option: plotCommandList.append('--showIntegralLegend=1')
    if 'postfit' in opt.option.lower(): plotCommandList.append(' --postFit=p')
    if 'nostat' in opt.option.lower(): plotCommandList.append('--removeMCStat')
    if 'nuisanceVariations' in opt.option: plotCommandList.append(' --nuisanceVariations') # TODO
    if 'cutlabel' in opt.option.lower(): plotCommandList.append(' --addCutLabels') # TODO
    if opt.paperStyle: plotCommandList.append(' --paperStyle') # TODO

    formatsToSave = 'png,root'
    if 'saveC'   in opt.option: formatsToSave += ',C'
    if 'savePDF' in opt.option: formatsToSave += ',pdf'
    plotCommandList.append('--fileFormats=\''+formatsToSave+'\'')

    configFile = commonTools.compileConfigurations(opt, 'plots', year, tag, sigset, fileset=fileset, plotPath=plotsDir)

    os.system(' '.join(plotCommandList))

    if not opt.keepallplots:
        plotToDelete = 'c_' if ('SM' in opt.sigset or 'keepratioplots' in opt.option) else 'cratio_'
        for plot2delete in [ plotToDelete, 'log_'+plotToDelete, 'cdifference_', 'log_cdifference_' ]:
            os.system('rm '+plotsDir+'/'+plot2delete+'*')

    commonTools.cleanConfigs(opt, configFile)

# Plot shape nuisances

def plotNuisances(opt):

   opt.fileset = commonTools.setFileset(opt.fileset, opt.sigset)
   opt.samplesFile = commonTools.getCfgFileName(opt, 'samples')
   opt.option += 'keepratioplots'

   yearList = opt.year.split('-') if 'merge' not in opt.option else [ opt.year ]

   for year in yearList:
       for tag in opt.tag.split('-'):

           optAux = copy.deepcopy(opt)
           optAux.year, optAux.tag = year, tag
     
           singleNuisances = {}

           if year.split('-')>1:

               outputNuisances =  '_'.join([ 'nuisances', year, tag, opt.sigset+'.py' ])
               commonTools.mergeDataTakingPeriodShapes(opt, year, tag, opt.fileset[1:], '', 'None', commonTools.getCfgFileName(opt, 'nuisances'), outputNuisances, opt.verbose)

               samples, cuts, variables = commonTools.getDictionaries(optAux, 'variables')
               nuisances = {}
               handle = open(outputNuisances,'r')
               exec(handle)
               handle.close()
               os.system('rm -f '+outputNuisances)

           else:

               samples, cuts, variables, nuisances = commonTools.getDictionaries(optAux)

           for nuisance in nuisances:
               if nuisance=='stat' or ('type' in nuisances[nuisance] and nuisances[nuisance]['type']=='shape'):
                   singleNuisanceName = 'statistics' if nuisance=='stat' else nuisances[nuisance]['name']
                   if 'nuisances:' not in opt.option or singleNuisanceName in opt.option:
                       nuisanceName = 'statistics' if nuisance=='stat' else nuisance
                       if singleNuisanceName not in singleNuisances:
                           singleNuisances[singleNuisanceName] = { }
                       singleNuisances[singleNuisanceName][nuisanceName] = nuisances[nuisance]

           for singleNuisance in singleNuisances:

               optAux.option = opt.option if singleNuisance=='statistics' else opt.option+'nuisanceVariations'

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
                   optAux.sigset = samplesToPlot
                   mkPlot(optAux, year, tag, optAux.sigset, singleNuisanceFile, extraOutDirFlag='_'+singleNuisance)

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

    commandList = [ commonTools.setupCombineCommand(opt, '\n') ]
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

            signals = commonTools.getDictionariesInLoop(opt, yearInFitList[0], tag, opt.sigset, 'samples')
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

                            samples, cuts, variables = commonTools.getDictionariesInLoop(opt, year, tag, sigset, 'variables', 'X')
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
                                            optAux = copy.deepcopy(opt)
                                            optAux.year, optAux.tag, optAux.sigset, optAux.baseDir = year, combinetag, sigset, os.getenv('PWD')
                                            postFitShapeFileFullPath = commonTools.mergeDirPaths(optAux.baseDir, postFitShapeFile)
                                            mergePostFitShapes(optAux, postFitShapeFileFullPath, signal, mlfitDir, cardsDir, '*', cut, variable, datacardNameStructure)

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

        for year in opt.year.split('-'):
            for tag in opt.tag.split('-'):
                mkPlot(opt, year, tag, opt.sigset)

### Datacards

def datacards(opt, signal='', combineOutDir='cardsdir', dryRun=False):

    fileset = commonTools.getFileset(opt.fileset, opt.sigset)

    if signal!='': signalList = [ signal ]
    else: signalList = commonTools.getSignalList(opt)

    datacardsCommandList = []

    blindData = '' if opt.unblind else ' --blindData '

    opt.cardsdir = commonTools.mergeDirPaths(opt.baseDir, opt.cardsdir)
    opt.shapedir = commonTools.mergeDirPaths(opt.baseDir, opt.shapedir)

    for signal in signalList:

        sigset = commonTools.getPerSignalSigset(fileset, opt.sigset, signal)
        signalWorkDir = commonTools.mergeDirPaths(opt.baseDir, commonTools.getSignalDir(opt, opt.year, opt.tag, signal, combineOutDir))

        for year in opt.year.split('-'):

            datacardsWorkDir = '/'.join([ signalWorkDir, year ])
            outputDir = commonTools.getSignalDir(opt, year, opt.tag, signal, 'cardsdir')
            datacardCommandList = [ 'cd '+datacardsWorkDir ]
            datacardCommandList.append('pwd; echo '+outputDir+';mkdir -p '+outputDir)
            datacardCommandList.append('mkDatacards --outputDirDatacard='+outputDir)
            datacardCommandList.append('cd '+opt.baseDir)

            if dryRun: 
                datacardsCommandList.extend(datacardCommandList) 

            else:
                datacardsConfigsDir = '/'.join([ datacardsWorkDir, 'configs' ]) 
                os.system('mkdir -p '+datacardsConfigsDir)
                configFile = commonTools.compileConfigurations(opt, 'datacards', year, opt.tag, sigset, fileset, configsFolder=datacardsConfigsDir)
                os.system('\n'.join(datacardCommandList))
                commonTools.deleteDirectory(datacardsWorkDir, opt.force)

    if dryRun: return datacardsCommandList

### Batch

def submitJobs(opt, jobName, jobTag, targetList, splitBatch, jobSplit, nThreads):

    opt.batchQueue = commonTools.batchQueue(opt, opt.batchQueue)

    jobs = batchJobs(jobName,jobTag,['ALL'],list(targetList.keys()),splitBatch,'',JOB_DIR_SPLIT_READY=jobSplit)
    jobs.nThreads = nThreads

    for signal in targetList:
        jobs.Add('ALL', signal, targetList[signal])

    if not opt.dryRun:
        jobs.Sub(opt.batchQueue,opt.IiheWallTime,True)

