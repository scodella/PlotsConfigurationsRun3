import os
import copy
import PlotsConfigurations.Tools.commonTools as commonTools
import PlotsConfigurations.Tools.latinoTools as latinoTools
from LatinoAnalysis.Tools.batchTools import *

def submitCombineJobs(opt, jobName, jobTag, combineJobs):

    nThreads = 1
    splitBatch =  'Targets'
    jobSplit = True if opt.sigset!='' and opt.sigset!='SM' else False
    
    latinoTools.submitJobs(opt, jobName, jobTag, combineJobs, splitBatch, jobSplit, nThreads)

def getLimitRun(unblind):

    return 'Both' if unblind else 'Blind'

def prepareDatacards(opt, signal, dryRun=False):

    prepareDatacardCommandList = [ ]

    if not opt.interactive:
        prepareDatacardCommandList.append('cd '+opt.combineTagDir)

    prepareDatacardCommandList.extend(latinoTools.datacards(opt, signal, True))

    prepareDatacardCommand = '\n'.join(prepareDatacardCommandList)

    if dryRun: return prepareDatacardCommand
    else: os.system(prepareDatacardCommand)

def getDatacardList(opt, signal):

    datacardList = [ ]

    addYearToDatacardName = len(opt.year.split('-'))>1

    for year in opt.year.split('-'):

        inputDatacardDir = commonTools.mergeDirPaths(opt.baseDir, commonTools.getSignalDir(opt, year, opt.tag, signal, 'cardsdir'))
        samples, cuts, variables = commonTools.getDictionariesInLoop(opt.configuration, year, opt.tag, 'SM', 'variables', opt.combineAction)

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

    combineDatacardCommandList = [ commonTools.setupCombineCommand(opt) ]

    signalOutputDir = commonTools.getSignalDir(opt, opt.year, opt.tag, signal, 'combineOutDir')
    combineDatacardCommandList.extend([ 'mkdir -p '+signalOutputDir, 'cd '+signalOutputDir ])

    combineDatacardCommandList.append('combineCards.py '+' '.join(getDatacardList(opt, signal))+' > combinedDatacard.txt')

    combineDatacardCommand = '\n'.join(combineDatacardCommandList)

    if dryRun: return combineDatacardCommand
    else: os.system(combineDatacardCommand)

def prepareJobDirectory(opt):

    os.system('mkdir -p '+opt.combineTagDir)
    for cfgFile in [ 'configuration', 'samples*', 'cuts', 'variables', 'nuisances', 'structure' ]:
        os.system('cp '+cfgFile+'.py '+opt.combineTagDir)
    os.system(' ; '.join([ 'cd '+opt.combineTagDir, 'ln -s -f '+opt.baseDir+'/Data', 'cd '+opt.baseDir ]))

def runCombine(opt):

    if not commonTools.foundShapeFiles(opt, True): exit()

    if not opt.interactive and opt.action!='writeDatacards':
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

    opt2 = copy.deepcopy(opt)

    opt2.baseDir = os.getenv('PWD')
    opt2.cardsdir = commonTools.mergeDirPaths(opt2.baseDir, opt2.cardsdir)
    opt2.shapedir = commonTools.mergeDirPaths(opt2.baseDir, opt2.shapedir)

    opt2.fileset, baseSigset = latinoTools.getPerSignalSigset(opt.fileset, opt.sigset) 

    yearList = opt.year.split('-') if 'split' in opt.option else [ opt.year ]

    for year in yearList:
        combineJobs = { }
        for tag in opt.tag.split('-'):

            outtag = commonTools.getTagForDatacards(tag, opt.sigset)+commonTools.getCombineOptionFlag(opt.option)
            opt2.year, opt2.tag = year, outtag

            samples = commonTools.getSamples(opt2)

            if not opt.interactive: 
                commonTools.cleanLogs(opt2)
                opt2.combineTagDir = commonTools.mergeDirPaths(opt2.baseDir, commonTools.getSignalDir(opt2, year, outtag, '', 'combineOutDir'))
                if makeDatacards: prepareJobDirectory(opt2)

            combineCommandList = [ ]
            if makeDatacards:  combineCommandList.append(prepareDatacards(opt2, 'MASSPOINT', True))
            combineCommandList.append(combineDatacards(opt2, 'MASSPOINT', True))
            if runCombineJob: 
                combineCommandList.append(opt.combineCommand)
                if opt.combineAction=='impacts':
                   impactPlotDir = '/'.join([ opt2.baseDir, opt.plotsdir, year, 'Impacts' ])
                   os.system('mkdir -p '+impactPlotDir)
                   combineCommandList.append('mv impacts.pdf '+impactPlotDir+'/'+outtag+'_MASSPOINT.pdf')
                if cleanDatacards: combineCommandList.append('rm combinedDatacard.txt')
            combineCommandList.append( 'cd '+opt2.baseDir )
            if cleanDatacards: combineCommandList.append(commonTools.cleanSignalDatacards(opt2, year, outtag, 'MASSPOINT', True))

            combineCommand = '\n'.join(combineCommandList)

            for sample in samples:
                if samples[sample]['isSignal']:

                    if runCombineJob:
                        combineOutputFileName = commonTools.getCombineOutputFileName(opt2, sample)

                        if opt.reset: 
                            os.system('rm -f '+combineOutputFileName)
                        elif commonTools.isGoodFile(combineOutputFileName, 6000.):
                            continue

                    signalCombineCommand = combineCommand.replace('MASSPOINT', sample)

                    if opt.debug: print(signalCombineCommand)
                    elif opt.interactive: os.system(signalCombineCommand)
                    else:
                        if outtag.split('__')[0] not in combineJobs:
                            combineJobs[outtag.split('__')[0]] = {}
                        combineJobs[outtag.split('__')[0]][sample+outtag.replace(outtag.split('__')[0],'')] = signalCombineCommand

        if not opt.debug and not opt.interactive:
            if len(list(combineJobs.keys()))>0: 
                for tag in  combineJobs:
                    if len(list(combineJobs[tag].keys()))>0:
                        combineJobsForTag = {}
                        subJobsList = {}
                        for tagSample in combineJobs[tag]:
                            subTag = tagSample.split('____')[0]
                            if subTag not in combineJobsForTag: 
                                combineJobsForTag[subTag] = combineJobs[tag][tagSample] 
                                subJobsList[subTag] = tagSample.replace(subTag+'____','')
                            else: 
                                combineJobsForTag[subTag] += '\n'+combineJobs[tag][tagSample]
                                subJobsList[subTag] += '-'+tagSample.replace(subTag+'____','')
                        #for subTag in combineJobsForTag.keys(): combineJobsForTag[subTag+'____'+subJobsList[subTag]] = combineJobsForTag.pop(subTag)
                        submitCombineJobs(opt, opt.combineAction, year+tag, combineJobsForTag)
                    else:
                        print('Nothing left to submit for tag', tag, 'in year', year)
            else:
                print('Nothing left to submit for tag list', opt.tag, 'in year', year)

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
    opt.combineCommand = ' '.join(['combine -M FitDiagnostics', fitOptions, 'combinedDatacard.txt' ])
    opt.combineOutDir = opt.mlfitdir

    runCombine(opt)

def impactsPlots(opt):

    opt.combineAction = 'impacts'
    opt.option += 'noshapes'
    if 'noautob' not in opt.option.lower(): opt.option += 'useautob'
    if 'norobust' not in opt.option.lower(): opt.option += 'dorobust'
    fitOptions = getFitOptions(opt.option.lower())
    stepList = [ 'text2workspace.py combinedDatacard.txt']
    stepList.append('combineTool.py -M Impacts -d combinedDatacard.root -m 125 --doInitialFit '+fitOptions)
    stepList.append('combineTool.py -M Impacts -d combinedDatacard.root -m 125 --doFits --parallel 100 '+fitOptions)
    stepList.append('combineTool.py -M Impacts -d combinedDatacard.root -m 125 -o impacts.json '+fitOptions)
    stepList.append('plotImpacts.py -i impacts.json -o impacts')
    opt.combineCommand = ' ; '.join(stepList)
    opt.combineOutDir = opt.impactdir

    runCombine(opt)

def saveNuisancesPlots(opt):

    plotRootFile = commonTools.openRootFile(commonTools.getSignalDir(opt,opt.year,opt.tag,opt.sigset,'mlfitdir')+'/plots'+commonTools.getCombineOptionFlag(opt.option)+'.root')
    for canvasName in [ 'asdf', 'nuisances', 'post_fit_errs' ]:
        nuisancePlot = plotRootFile.Get(canvasName)
        nuisancePlot.Print('/'.join([ opt.plotsdir, opt.year, 'Impacts', 'Nuisances', '' ])+'_'.join([ opt.tag, opt.sigset, canvasName ])+'.png')

def diffNuisances(opt):

    opt.baseDir = os.getenv('PWD')
    commandList = [ commonTools.setupCombineCommand(opt, ' ; ') ]
    nuisCommand = 'python $CMSSW_BASE/src/HiggsAnalysis/CombinedLimit/test/diffNuisances.py  -a fitDiagnostics.root -g plots.root > diffNuisances.txt'
    outputString = commonTools.getCombineOptionFlag(opt.option)
    if 'skipfitb' in opt.option.lower(): nuisCommand = nuisCommand.replace(' > ', ' --skipFitB > ')
    if 'skipfits' in opt.option.lower(): nuisCommand = nuisCommand.replace(' > ', ' --skipFitS > ')
    nuisCommand = nuisCommand.replace('.root', outputString+'.root').replace('.txt', outputString+'.txt')
    plotCommandList = [ commonTools.cdWorkDir(opt) ]

    yearList = opt.year.split('-') if 'split' in opt.option else [ opt.year ]
    for year in yearList:

        plotOutputDir = '/'.join([ opt.plotsdir, year, 'Impacts', 'Nuisances', '' ])
        os.system('mkdir -p '+plotOutputDir)
        commonTools.copyIndexForPlots(opt.plotsdir, plotOutputDir)

        for tag in opt.tag.split('-'):

            signals = commonTools.getSignals(opt)
            for signal in signals:

                commandList.extend([ 'cd '+commonTools.getSignalDir(opt,year,tag,signal,'mlfitdir'), nuisCommand, 'cd -' ])

                plotCommandList.append('./runAnalysis.py --action=saveNuisancesPlots --year='+year+' --tag='+tag+' --sigset='+signal)

    os.system(' ; '.join(commandList+plotCommandList))

