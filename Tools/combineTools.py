import os
import copy
import commonTools
import latinoTools

def submitCombineJobs(opt, year, combineJobs):

    for coreTag in  combineJobs:
        if len(list(combineJobs[coreTag].keys()))==0:
            print('Nothing left to submit for year '+year+', tag '+coreTag)
            continue
        combineJobsForTag = {}
        for signalSubTag in combineJobs[coreTag]:
            combineJobsForTag[signalSubTag] = combineJobs[coreTag][signalSubTag]
        commonTools.submitJobs(opt, opt.combineAction, year+'/'+coreTag, combineJobsForTag)

def getLimitRun(unblind):

    return 'Both' if unblind else 'Blind'

def prepareDatacards(opt, signal, dryRun=False):

    prepareDatacardCommandList = [ ]

    prepareDatacardCommandList.extend(latinoTools.datacards(opt, signal, 'combineOutDir', True))

    prepareDatacardCommand = '\n'.join(prepareDatacardCommandList)

    if dryRun: return prepareDatacardCommand
    else: os.system(prepareDatacardCommand)

def getDatacardList(opt, signal):

    datacardList = [ ]

    addYearToDatacardName = len(opt.year.split('-'))>1

    for year in opt.year.split('-'):

        inputDatacardDir = commonTools.mergeDirPaths(opt.baseDir, commonTools.getSignalDir(opt, year, opt.tag, signal, 'cardsdir'))
        samples, cuts, variables = commonTools.getDictionariesInLoop(opt, year, opt.tag, opt.sigset, 'variables') 

        datacardNameStructure = latinoTools.getDatacardNameStructure(addYearToDatacardName, len(list(cuts.keys()))>1, len(list(variables.keys()))>1)
        datacardNameStructure = datacardNameStructure.replace('year', year)

        for cut in cuts:
            for variable in variables:
                if 'cuts' not in variables[variable] or cut in variables[variable]['cuts']:

                    datacardName = datacardNameStructure.replace('cut', cut).replace('variable', variable)
                    datacardFile = '/'.join([ inputDatacardDir, cut, variable, 'datacard.txt' ])
                    datacardList.append(datacardName+'='+datacardFile)

    return datacardList

def combineDatacards(opt, signal, dryRun=False):

    combineDatacardCommandList = [ 'mkdir -p '+opt.signalOutputDir ]

    combineDatacardScript = opt.signalOutputDir+'/combineDatacards.sh'
    combineDatacardScriptList = commonTools.setupCombineCommand(opt)
    combineDatacardScriptList.append('cd '+opt.signalOutputDir)
    combineDatacardScriptList.append('combineCards.py '+' '.join(getDatacardList(opt, signal))+' > combinedDatacard.txt')
    combineDatacardCommandList.extend(commonTools.buildExternalScript(combineDatacardScript, combineDatacardScriptList, 'list'))

    combineDatacardCommandList.append('env -i '+commonTools.getAbsPath(combineDatacardScript))
    combineDatacardCommandList.extend([ 'cd '+opt.signalOutputDir, 'rm combineDatacards.sh' ])

    combineDatacardCommand = '\n'.join(combineDatacardCommandList)

    if dryRun: return combineDatacardCommand
    else: os.system(combineDatacardCommand)

def buildCombineScript(opt, signal, dryRun=False):

    combineScript = opt.signalOutputDir+'/combineScript.sh'
    combineScriptList = commonTools.setupCombineCommand(opt)
    combineScriptList.append('cd '+opt.signalOutputDir)
    combineScriptList.append(opt.combineCommand.replace('YEAR', opt.year).replace('TAG',opt.tag))
    combineCommandList = commonTools.buildExternalScript(combineScript, combineScriptList, 'list')

    combineCommandList.append('env -i '+commonTools.getAbsPath(combineScript))
    combineCommandList.append('rm combineScript.sh')

    combineCommand = '\n'.join(combineCommandList)

    if dryRun: return combineCommand
    else: os.system(combineCommand)

def runCombine(opt):

    if not commonTools.foundShapeFiles(opt, True): exit()

    if not opt.interactive and opt.action!='writeDatacards' and not opt.dryRun:
        commonTools.checkProxy(opt)

    if not hasattr(opt, 'combineAction'):
        if 'limit' in opt.option: limits(opt)
        elif 'goffit' in opt.option: goodnessOfFit(opt)
        elif 'mlfits' in opt.option: mlfits(opt)
        elif 'impact' in opt.option: impactsPlots(opt)
        else: print('Please, speficy if you want to compute limits, make ML fits, or produce impacts plots')
        exit()

    opt.logprocess = opt.combineAction
    if opt.combineLocation=='COMBINE': opt.combineLocation = os.getenv('PWD').split('/src/')[0]+'/src/'

    makeDatacards  = 'skipdatacard' not in opt.option.lower() and 'skipdc' not in opt.option.lower()
    cleanDatacards = 'keepdatacard' not in opt.option.lower() and 'keepdc' not in opt.option.lower()
    runCombineJob  = 'onlydatacard' not in opt.option.lower() and 'onlydc' not in opt.option.lower()

    if not runCombineJob:
        opt.interactive = True
        cleanDatacards = False

    optAux = copy.deepcopy(opt)

    optAux.cardsdir = commonTools.mergeDirPaths(optAux.baseDir, optAux.cardsdir)
    optAux.shapedir = commonTools.mergeDirPaths(optAux.baseDir, optAux.shapedir)

    optAux.fileset = commonTools.getFileset(opt.fileset, opt.sigset) 

    yearList = opt.year.split('-') if 'split' in opt.option else [ opt.year ]

    for year in yearList:
        combineJobs = { }
        for tag in opt.tag.split('-'):

            outtag = commonTools.getTagForDatacards(tag, opt.sigset)+commonTools.getCombineOptionFlag(opt.option)
            optAux.year, optAux.tag = year, outtag

            if not opt.interactive:
                coreTag, subTag = commonTools.getTagStructureForCombine(optAux.tag, 'SIGNAL', optAux.sigset)
                if coreTag not in combineJobs: combineJobs[coreTag] = {}
                commonTools.cleanLogs(optAux, optAux.combineAction)

            optAux.signalOutputDir = commonTools.getSignalDir(opt, optAux.year, optAux.tag, 'SIGNAL', 'combineOutDir')

            combineCommandList = [ ]
            if makeDatacards:  combineCommandList.append(prepareDatacards(optAux, 'SIGNAL', True))
            combineCommandList.append(combineDatacards(optAux, 'SIGNAL', True))
            if runCombineJob: 
                combineCommandList.append(buildCombineScript(optAux, 'SIGNAL', True))
                if cleanDatacards: combineCommandList.append('rm combinedDatacard.txt')
            if makeDatacards:
                for period in year.split('-'): combineCommandList.append(commonTools.deleteDirectory(period, opt.force, True))
            combineCommandList.append( 'cd '+optAux.baseDir )
            if cleanDatacards: combineCommandList.append(commonTools.cleanSignalDatacards(optAux, year, outtag, 'SIGNAL', True))

            combineCommand = '\n'.join(combineCommandList)

            for signal in commonTools.getSignalList(optAux):

                if runCombineJob:
                    combineOutputFileName = commonTools.getCombineOutputFileName(optAux, signal)

                    if opt.reset: os.system('rm -f '+combineOutputFileName)
                    elif commonTools.isGoodFile(combineOutputFileName, 6000.): continue

                if makeDatacards:                    
                    signalWorkDir = commonTools.getSignalDir(optAux, year, outtag, signal, 'combineOutDir')
                    for period in year.split('-'):
                        datacardsConfigsDir = '/'.join([ signalWorkDir, period, 'configs' ])
                        os.system('mkdir -p '+datacardsConfigsDir)
                        sigset = commonTools.getPerSignalSigset(optAux.fileset, optAux.sigset, signal) 
                        configFile = commonTools.compileConfigurations(optAux, 'datacards', period, outtag, sigset, optAux.fileset, configsFolder=datacardsConfigsDir)

                signalCombineCommand = combineCommand.replace('SIGNAL', signal)

                if opt.debug: print(signalCombineCommand)
                elif opt.interactive: os.system(signalCombineCommand)
                else:
                    signalSubTag = subTag.replace('SIGNAL', signal)
                    if signalSubTag not in combineJobs[coreTag]:
                        combineJobs[coreTag][signalSubTag] = signalCombineCommand
                    combineJobs[coreTag][signalSubTag] += '\n'+signalCombineCommand

        if not opt.debug and not opt.interactive: submitCombineJobs(opt, year, combineJobs)

def writeDatacards(opt):

    opt.combineAction = 'datacard'
    opt.option += 'onlydatacards'
    opt.combineCommand = 'dummy'
    opt.combineOutDir = opt.cardsdir

    runCombine(opt)

def limits(opt):

    opt.combineAction = 'limits'
    if 'toy' in opt.option.lower():
        opt.batchQueue = 'nextweek'
        if 'btoy' in opt.option.lower(): limitMethod = '-M BayesianToyMC'
        else: limitMethod = '-M HybridNew --LHCmode LHC-limits'
    else:
        limitRun = getLimitRun(opt.unblind) 
        limitMethod = ' '.join([ '-M AsymptoticLimits', '--run '+limitRun.lower(), '-n _'+limitRun ])
    if 'asimovb' in opt.option: limitMethod += ' -t -1 --expectSignal  0'
    opt.combineCommand = ' '.join([ 'combine', limitMethod, 'combinedDatacard.txt' ])
    opt.combineOutDir = opt.limitdir

    runCombine(opt)

def getFitOptions(options):

    optionList = []
    if 'noshapes' not in options: 
        optionList.extend([ '--saveShapes', '--saveWithUncertainties', '--saveOverallShapes', '--plots' ])
        if 'asimov' in options: optionList.extend([ '--numToysForShapes 200' ])
    if 'skipbonly' in options: optionList.append('--skipBOnlyFit')
    if 'asimov' in options:
        if 'asimovb' in options: optionList.append('-t -1 --expectSignal  0')
        if 'asimovs' in options: optionList.append('-t -1 --expectSignal  1')
        if 'asimovi' in options: optionList.append('-t -1 --expectSignal 15')
        optionList.append('-n '+commonTools.getCombineOptionFlag(options))
    if 'useautob' in options: optionList.append('--autoBoundsPOIs="*"')
    if 'negsign'  in options: optionList.append('--rMin -10')
    if 'usedms'   in options: optionList.append('--cminDefaultMinimizerStrategy 0')
    if 'dorobfit' in options: optionList.append('--robustFit 1')
    return ' '.join(optionList)

def goodnessOfFit(opt):

    opt.combineAction = 'goffit'
    fitOptions = getFitOptions(opt.option.lower())
    algo = 'AD' if 'AD' in opt.option else 'KS' if 'KS' in opt.option else 'saturated'
    toy = '-t 100' if 'toy' in opt.option or 'toy' in opt.tag else '' 
    opt.combineCommand = ' '.join(['combine -M GoodnessOfFit --algo='+algo+' '+toy+' combinedDatacard.txt' ])
    opt.combineOutDir = opt.gofitdir

    runCombine(opt)

def mlfits(opt):

    opt.combineAction = 'mlfits'
    if 'nodms' not in opt.option.lower(): opt.option += 'usedms'
    fitOptions = getFitOptions(opt.option.lower())
    opt.combineCommand = ' '.join(['combine -M FitDiagnostics', fitOptions, '-n \'\'', 'combinedDatacard.txt' ])
    opt.combineOutDir = opt.mlfitdir

    runCombine(opt)

def impactsPlots(opt):

    opt.combineAction = 'impacts'
    opt.option += 'noshapes'
    if 'noautob' not in opt.option.lower(): opt.option += 'useautob'
    if 'norobust' not in opt.option.lower(): opt.option += 'dorobfit'
    fitOptions = getFitOptions(opt.option.lower())
    stepList = [ 'text2workspace.py combinedDatacard.txt']
    stepList.append('combineTool.py -M Impacts -d combinedDatacard.root -m 125 --doInitialFit '+fitOptions)
    stepList.append('combineTool.py -M Impacts -d combinedDatacard.root -m 125 --doFits --parallel 100 '+fitOptions)
    stepList.append('combineTool.py -M Impacts -d combinedDatacard.root -m 125 -o impacts.json '+fitOptions)
    stepList.append('mkdir -p '+'/'.join([ opt.baseDir, opt.plotsdir, 'YEAR', 'Impacts' ]))
    stepList.append('plotImpacts.py -i impacts.json -o '+impactPlotDir+'/TAG_SIGNAL')
    opt.combineCommand = ' ; '.join(stepList)
    opt.combineOutDir = opt.impactdir

    runCombine(opt)

def saveNuisancesPlots(opt):

    plotRootFile = commonTools.openRootFile(commonTools.getSignalDir(opt,opt.year,opt.tag,opt.sigset,'mlfitdir')+'/plots'+commonTools.getCombineOptionFlag(opt.option)+'.root')
    for canvasName in [ 'asdf', 'nuisances', 'post_fit_errs' ]:
        nuisancePlot = plotRootFile.Get(canvasName)
        nuisancePlot.Print('/'.join([ opt.plotsdir, opt.year, 'Impacts', 'Nuisances', '' ])+'_'.join([ opt.tag, opt.sigset, canvasName ])+'.png')

def diffNuisances(opt): # TODO need to make it work outside CMSSW 

    opt.baseDir = os.getenv('PWD')
    commandList = [ commonTools.setupCombineCommand(opt, '; ') ]
    nuisCommand = 'python $CMSSW_BASE/src/HiggsAnalysis/CombinedLimit/test/diffNuisances.py  -a fitDiagnostics.root -g plots.root > diffNuisances.txt'
    outputString = commonTools.getCombineOptionFlag(opt.option)
    if 'skipfitb' in opt.option.lower(): nuisCommand = nuisCommand.replace(' > ', ' --skipFitB > ')
    if 'skipfits' in opt.option.lower(): nuisCommand = nuisCommand.replace(' > ', ' --skipFitS > ')
    nuisCommand = nuisCommand.replace('.root', outputString+'.root').replace('.txt', outputString+'.txt')
    plotCommandList = [ commonTools.cdWorkDir(opt) ]

    yearList = opt.year.split('-') if 'split' in opt.option else [ opt.year ]
    for year in yearList:

        plotOutputDir = '/'.join([ opt.plotsdir, year, 'Impacts', 'Nuisances', '' ])
        commonTools.copyIndexForPlots(plotOutputDir)

        for tag in opt.tag.split('-'):

            signals = commonTools.getSignalList(opt)
            for signal in signals:

                commandList.extend([ 'cd '+commonTools.getSignalDir(opt,year,tag,signal,'mlfitdir'), nuisCommand, 'cd -' ])

                plotCommandList.append('./runAnalysis.py --action=saveNuisancesPlots --year='+year+' --tag='+tag+' --sigset='+signal)

    os.system(' ; '.join(commandList+plotCommandList))
