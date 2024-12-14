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
    opt.treeName = 'btagana/ttree'
    opt.unblind = True
    opt.campaign = opt.year

    opt.dataConditionScript = '../../../LatinoAnalysis/NanoGardener/python/data/dataTakingConditionsAnalyzer.py'
    opt.combineLocation = '/afs/cern.ch/work/s/scodella/SUSY/CMSSW_14_1_0_pre4/src' 

    opt.filesToExec = {}
    if 'Summer23' in opt.campaign:
        opt.filesToExec['samples.py'] = 'samples_Run2023-130X.py'

### Shapes, kinematic weights and prefit plots

def bTagPerfShapes(opt, tag, action):

    commonTools.getConfigParameters(opt, [ 'systematicVariations' ])

    for selection in opt.systematicVariations:

        optAux = copy.deepcopy(opt)
        optAux.tag = tag.replace(tag.split('.')[0], tag.split('.')[0]+selection)

        sigsets = [ 'MC', 'Data' ] if opt.sigset=='SM' else [ opt.sigset ]
        for sigset in sigsets:

            optAux.sigset = sigset
            if sigset=='Data' and '.' in tag and 'Light' not in tag: optAux.tag = optAux.tag.split('.')[0]
            if 'MC' in sigset and 'Light' in opt.tag: optAux.batchQueue = 'testmatch'
            if 'shapes' in action: latinoTools.shapes(optAux)
            if opt.merge and 'Light' in optAux.tag: mergeLightShapes(optAux)

def makeShapes(opt):

    for tag in opt.tag.split('-'):
        bTagPerfShapes(opt, tag, 'shapes')

def mergeShapes(opt):

    opt.merge = True
    for tag in opt.tag.split('-'):
        bTagPerfShapes(opt, tag, 'mergeShapes')

def checkShapes(opt):

    opt.checkjobs = True
    makeShapes(opt)

def recoverShapes(opt):

    opt.recover = True
    makeShapes(opt)

def resubmitShapes(opt):

    opt.reset = True
    makeShapes(opt)

def mergeLightShapes(opt): # TODO port to Run3 if needed

    if 'PtRelLight' not in opt.tag:
        print('Please choose a tag (PtRelLightKinematics or PtRelLightTemplates)')
        exit()

    outtag = opt.tag.replace('Light', 'MergedLight')

    samples, cuts, variables, nuisances = commonTools.getDictionariesInLoop(opt, opt.year, opt.tag, opt.sigset, 'nuisances')

    for sample in samples:    

        inputFile  = commonTools.openSampleShapeFile(opt.shapedir, opt.year, opt.tag, sample)
        outputFile = commonTools.openSampleShapeFile(opt.shapedir, opt.year, outtag, sample, 'recreate')

        for cut in cuts:

            outputFile.mkdir(cut)

            mergedShapes = {}

            for variable in variables:
                if 'cuts' not in variables[variable] or cut in variables[variable]['cuts']:

                    shapeName = '_'.join([ variableString for variableString in variable.split('_') if not variableString.isdigit() ])
                    if shapeName not in mergedShapes: mergedShapes[shapeName] = {}

                    if 'histo_'+sample not in mergedShapes[shapeName]:
                        mergedShapes[shapeName]['histo_'+sample] = inputFile.Get('/'.join([ cut, variable, 'histo_'+sample ]))          
                    else:
                        mergedShapes[shapeName]['histo_'+sample].Add(inputFile.Get('/'.join([ cut, variable, 'histo_'+sample ])))
            
                    for nuisance in nuisances:
                        if nuisance!='stat' and nuisances[nuisance]['type']=='shape':
                            if 'cuts' not in nuisances[nuisance] or cut in nuisances[nuisance]['cuts']:
                                if sample in nuisances[nuisance]['samples']:
                                    for variation in [ 'Up', 'Down' ]:
                                           
                                        nuisanceHistoName = 'histo_'+sample+'_'+nuisances[nuisance]['name']+variation
                                        if nuisanceHistoName not in mergedShapes[shapeName]:
                                            mergedShapes[shapeName][nuisanceHistoName] = inputFile.Get('/'.join([ cut, variable, nuisanceHistoName ]))
                                        else:
                                            mergedShapes[shapeName][nuisanceHistoName].Add(inputFile.Get('/'.join([ cut, variable, nuisanceHistoName ])))

            for variable in mergedShapes:
                
                outputFile.mkdir(cut+'/'+variable)
                outputFile.cd(cut+'/'+variable)

                for histo in mergedShapes[variable]:
                    mergedShapes[variable][histo].Write(histo)

        inputFile.Close()
        outputFile.Close()

def shapesForFit(opt):

    if 'PtRel' in opt.tag: ptRelInput(opt)
    else: system8Input(opt) 

def ptRelInput(opt): # TODO port part for light jets

    commonTools.getConfigParameters(opt, [ 'systematicVariations', 'templateTreatments', 'jetPtBins', 'bTagWorkingPoints', 'bTemplateCorrector' ])

    doBCorrections, doLCorrections = False, False
    templateTreatmentDict = {}
    templateTreatmentFlag = ''

    for treatment in opt.templateTreatments:
        option = opt.option.lower()
        if treatment in option:

            templateTreatmentDict[treatment] = []
            templateTreatmentFlag += treatment.capitalize()

            samplesForTreatment = option.split(treatment)[-1]
            for othertreatment in opt.templateTreatments: samplesForTreatment = samplesForTreatment.split(othertreatment)[0]

            for sample in [ 'ljets', 'bjets' ]:
               if sample.replace('jets','') in samplesForTreatment: 
                   templateTreatmentDict[treatment].append(sample)
                   templateTreatmentFlag += sample.replace('jets','').upper()
                   if sample=='ljets': doLCorrections = True
                   if sample=='bjets': doBCorrections = True

            if len(templateTreatmentDict[treatment])==0: 
                print('Error: no sample found for template treatment', treatment)
                exit()

    if opt.verbose: 
        print('Preparing fit templates with templateTreatmentFlag =', templateTreatmentFlag)
        print('Reading templates')

    outputTemplates = {}

    for datatype in [ 'MuEnriched', 'Inclusive' ]:
        if datatype=='Inclusive' and not doLCorrections: continue
        for sigset in [ 'MC', 'Data' ]:
            for selection in opt.systematicVariations:

                if datatype=='Inclusive' and 'AwayJet' in selection: continue

                optAux = copy.deepcopy(opt)
                optAux.tag = opt.tag.replace(opt.tag.split('.')[0], opt.tag.split('.')[0]+selection)
                if sigset=='Data' and datatype=='MuEnriched': optAux.tag = optAux.tag.split('.')[0]
                if datatype=='Inclusive': optAux.tag = optAux.tag.replace('Templates','MergedLightTemplates').replace('mujet','lightjet')
                optAux.sigset = sigset

                samples, cuts, variables, nuisances = commonTools.getDictionaries(optAux)

                if datatype=='Inclusive':
                    if not commonTools.foundShapeFile(optAux.shapedir, optAux.year, optAux.tag, sigset) or opt.reset:
                        optAux.tag = optAux.tag.replace('MergedLight','Light')
                        mergeLightShapes(optAux)
                        optAux.tag = optAux.tag.replace('PtRelLight','PtRelMergedLight')

                inputTemplateFile = commonTools.openShapeFile(optAux.shapedir, optAux.year, optAux.tag, sigset)

                for ptBin in list(opt.jetPtBins.keys()):
                    for btagWP in list(opt.bTagWorkingPoints.keys()):
                        for btagCut in [ 'Pass', 'Fail' ]:

                            cutName = '_'.join([x for x in [ ptbin, btagwp, btagselection, selection ] if x!=''])
                            if cutName not in outputTemplates: outputTemplates[cutName] = {}

                            if opt.verbose: print('     selection', selection, ' and cut', cutName)

                            inputCutName = '_'.join([ ptBin, btagWP, btagCut ]) if datatype=='MuEnriched' else ptBin
                            variable = 'ptrel' if datatype=='MuEnriched' else '_'.join([ 'ptrel', ptBin ])

                            for sample in samples:

                                histoName = '/'.join([ inputCutName, variable, 'histo_' + sample ])
                                template = copy.deepcopy(inputTemplateFile.Get(histoName))

                                template.SetName('_'.join([ 'histo', sample ]))
                                template.SetTitle('_'.join([ 'histo', sample ]))
                                outputTemplates[cutName][template.GetName()] = template

                                for nuisance in nuisances:
                                    if nuisance=='stat': pass
                                    elif nuisances[nuisance]['type']=='shape':
                                        if 'cuts' not in nuisances[nuisance] or inputCutName in nuisances[nuisance]['cuts']:
                                            if sample in nuisances[nuisance]['samples']:
                                                for variation in [ 'Up', 'Down' ]:

                                                    templateNuisance = copy.deepcopy(inputTemplateFile.Get(histoName + '_' + nuisances[nuisance]['name'] + variation))
                                                    outputTemplates[cutName][templateNuisance.GetName().split('/')[-1]] = templateNuisance

                                    elif nuisances[nuisance]['type']=='lnN':
                                        if '2D' in opt.option and ('ljets' in nuisances[nuisance]['samples'] or 'cjets' in nuisances[nuisance]['samples']):
                                            if sample=='ljets' or sample=='cjets':
                                                for variation in [ 'Up', 'Down' ]:

                                                    centralTemplate = copy.deepcopy(inputTemplateFile.Get(histoName))
                                                    if sample in nuisances[nuisance]['samples']:
                                                        if variation=='Up': centralTemplate.Scale(float(nuisances[nuisance]['samples'][sample]))
                                                        else: centralTemplate.Scale(2.-float(nuisances[nuisance]['samples'][sample]))
                                                    centralTemplate.SetName('_'.join([ 'histo', sample, nuisances[nuisance]['name']+variation]))
                                                    centralTemplate.SetTitle('_'.join([ 'histo', sample, nuisances[nuisance]['name']+variation]))
                                                    outputTemplates[cutName][centralTemplate.GetName()] = centralTemplate

    if opt.verbose: print('Normalizing templates')

    cutNameList = list(outputTemplates.keys())

    dataPS, jetPS, jetYields = {}, {}, {}
    for cutName in cutNameList:
        
        errorDataYields = ctypes.c_double()
        dataYields = outputTemplates[cutName]['histo_DATA'].IntegralAndError(-1,-1,errorDataYields)
        dataPS[cutName] = pow(dataYields/errorDataYields.value, 2)/dataYields

        if doLCorrections:
            jetCutName = cutName if 'histo_Jet' in outputTemplates[cutName] else '_'.join([ cutName.split('_')[x] for x in range(3) ])
            errorJetYields = ctypes.c_double()
            jetYields[cutName] = outputTemplates[jetCutName]['histo_Jet'].IntegralAndError(-1,-1,errorJetYields)
            jetPS[cutName] = pow(jetYields[cutName]/errorJetYields.value, 2)/jetYields[cutName]
                 
    for cutName in cutNameList:

        for template in outputTemplates[cutName]:
            if 'histo_Jet' in template: 
                outputTemplates[cutName][template].Scale(jetPS[cutName])
            elif 'histo_QCD' in template:
                qcdYields = outputTemplates[cutName][template].Integral(-1,-1)
                outputTemplates[cutName][template].Scale(jetPS[cutName]*jetYields[cutName]/qcdYields)
            else:
                outputTemplates[cutName][template].Scale(dataPS[cutName])

    if opt.verbose: print('Computing corrections')

    for cutName in cutNameList:

        if doLCorrections: 
            outputTemplates[cutName+'_CorrL'] = {}
            jetCutName = cutName if 'histo_Jet' in outputTemplates[cutName] else '_'.join([ cutName.split('_')[x] for x in range(3) ])
            qcdCutName = cutName if 'histo_QCD' in outputTemplates[cutName] else '_'.join([ cutName.split('_')[x] for x in range(3) ])
            jetHisto = copy.deepcopy(outputTemplates[jetCutName]['histo_Jet'])
            for template in list(outputTemplates[cutName].keys()):
                if 'histo_ljets' in template:

                    correctedHisto = copy.deepcopy(outputTemplates[cutName][template])

                    if template.replace('_ljets','_QCD') in outputTemplates[qcdCutName]:
                        qcdHisto = copy.deepcopy(outputTemplates[qcdCutName][template.replace('_ljets','_QCD')])
                    else: qcdHisto = copy.deepcopy(outputTemplates[qcdCutName]['histo_QCD'])

                    correctedHisto.Multiply(jetHisto)
                    correctedHisto.Divide(qcdHisto)   
                    outputTemplates[cutName+'_CorrL'][template] = correctedHisto

        if doBCorrections:
            outputTemplates[cutName+'_CorrB'] = {}
            cutNameCorrector = cutName.replace(cutName.split('_')[1],opt.bTemplateCorrector[cutName.split('_')[1]]).replace('Fail','Pass')
            for template in list(outputTemplates[cutName].keys()):
                if 'histo_bjets' in template:

                    dataHisto = copy.deepcopy(outputTemplates[cutNameCorrector]['histo_DATA'])
                    dataYields = dataHisto.Integral(-1,-1)

                    correctedHisto = copy.deepcopy(outputTemplates[cutName][template])

                    bHisto = copy.deepcopy(outputTemplates[cutNameCorrector][template])

                    if template.replace('_bjets','_cjets') in outputTemplates[cutNameCorrector]:
                        cHisto = copy.deepcopy(outputTemplates[cutNameCorrector][template.replace('_bjets','_cjets')])
                    else: cHisto = copy.deepcopy(outputTemplates[cutNameCorrector]['histo_cjets'])
 
                    if template.replace('_bjets','_ljets') in outputTemplates[cutNameCorrector]:
                        lHisto = copy.deepcopy(outputTemplates[cutNameCorrector][template.replace('_bjets','_ljets')])
                    else: lHisto = copy.deepcopy(outputTemplates[cutNameCorrector]['histo_ljets'])

                    mcYields = bHisto.Integral(-1,-1) + cHisto.Integral(-1,-1) + lHisto.Integral(-1,-1)
                    bHisto.Scale(dataYields/mcYields); cHisto.Scale(dataYields/mcYields); lHisto.Scale(dataYields/mcYields);
                    dataHisto.Add(cHisto,-1); dataHisto.Add(lHisto,-1);

                    correctedHisto.Multiply(dataHisto)
                    correctedHisto.Divide(bHisto)
                    outputTemplates[cutName+'_CorrB'][template] = correctedHisto

    if '2D' in opt.option:

        if opt.verbose: print('Merging light and c templates')

        for cutName in cutNameList:
            for template in list(outputTemplates[cutName].keys()):
                if 'ljets' in template:
                    outputTemplates[cutName][template].Add(outputTemplates[cutName][template.replace('ljets','cjets')])
                    if doLCorrections: outputTemplates[cutName+'_CorrL'][template].Add(outputTemplates[cutName][template.replace('ljets','cjets')])

    if opt.verbose: print('Saving templates', cutName)

    outtag = opt.tag.replace(opt.tag.split('.')[0], opt.tag.split('.')[0]+'ForFit')
    if '2D' in opt.option: outtag = outtag.replace('Templates', 'Templates2D')
    outtag = outtag.replace('Templates', 'Templates'+templateTreatmentFlag)
    ptRelTemplateFile = commonTools.openShapeFile(opt.shapedir, opt.year, outtag, opt.sigset, opt.fileset, 'recreate')

    for cutName in cutNameList:

        if opt.verbose: print('     Saving templates for cut', cutName, '\n')

        ptRelTemplateFile.mkdir(cutName)
        ptRelTemplateFile.mkdir(cutName+'/ptrel')
        ptRelTemplateFile.cd(cutName+'/ptrel')

        sampleCutName = { 'DATA' : '' }
        if '2D' not in opt.option: sampleCutName['cjets'] = ''
        sampleCutName['ljets'] = '_CorrL' if 'corr' in templateTreatmentDict and 'ljets' in templateTreatmentDict['corr'] else ''
        sampleCutName['bjets'] = '_CorrB' if 'corr' in templateTreatmentDict and 'bjets' in templateTreatmentDict['corr'] else ''

        for template in list(outputTemplates[cutName].keys()):
            sample = template.split('_')[1]
            if sample in sampleCutName:
                if opt.verbose: print('        ', cutName, sample, sampleCutName[sample], template)
                outputTemplates[cutName+sampleCutName[sample]][template].Write()

        if opt.verbose: print('\n')

        nuisCutNameList = [ cutName ]
        if 'syst' in templateTreatmentDict and len(cutName.split('_'))==3:
            for systSample in templateTreatmentDict['syst']:
            
                systCutName = cutName+'_Corr'+systSample.replace('jets','').upper()
                ptRelTemplateFile.mkdir(systCutName)
                ptRelTemplateFile.mkdir(systCutName+'/ptrel')
                ptRelTemplateFile.cd(systCutName+'/ptrel')

                sampleSystCutName = copy.deepcopy(sampleCutName)
                sampleSystCutName[systSample] = '_Corr'+systSample.replace('jets','').upper() if sampleCutName[systSample]=='' else ''

                for template in list(outputTemplates[cutName].keys()):
                    sample = template.split('_')[1]
                    if sample in sampleSystCutName:
                        if opt.verbose: print('        ', systCutName, sample, sampleSystCutName[sample], template)
                        outputTemplates[cutName+sampleSystCutName[sample]][template].Write()

                nuisCutNameList.append(systCutName)
                if opt.verbose: print('\n')

        if 'nuis' in templateTreatmentDict:
            for nuisSample in templateTreatmentDict['nuis']:

                correctionFlag = '_Corr'+nuisSample.replace('jets','').upper()
                nominalHisto = copy.deepcopy(outputTemplates[cutName]['histo_'+nuisSample])
                correctedHisto = copy.deepcopy(outputTemplates[cutName+correctionFlag]['histo_'+nuisSample])

                if sampleCutName[nuisSample]=='':
                    nominalHisto.SetName('histo_'+nuisSample+correctionFlag+'Down')
                    nominalHisto.SetTitle('histo_'+nuisSample+correctionFlag+'Down')
                    correctedHisto.SetName('histo_'+nuisSample+correctionFlag+'Up')
                    correctedHisto.SetTitle('histo_'+nuisSample+correctionFlag+'Up')
                else:
                    nominalHisto.SetName('histo_'+nuisSample+correctionFlag+'Up')
                    nominalHisto.SetTitle('histo_'+nuisSample+correctionFlag+'Up')
                    correctedHisto.SetName('histo_'+nuisSample+correctionFlag+'Down')
                    correctedHisto.SetTitle('histo_'+nuisSample+correctionFlag+'Down')

                for nuisCutName in nuisCutNameList:
                    ptRelTemplateFile.cd(nuisCutName+'/ptrel')
                    if opt.verbose: print('        ', cutName, nuisSample, correctionFlag, nominalHisto.GetName(), correctedHisto.GetName(), '->', nuisCutName)
                    nominalHisto.Write()
                    correctedHisto.Write()

        if opt.verbose: print('\n')

        if len(cutName.split('_'))==3:
            doneNuisance = []
            for nuisTemplate in list(outputTemplates[cutName].keys()):
                if len(nuisTemplate.split('_'))>2:

                    nuisance = nuisTemplate.replace('histo_'+nuisTemplate.split('_')[1]+'_','')
                    if cutName+'_'+nuisance in outputTemplates: continue
                    if nuisance in doneNuisance: continue

                    ptRelTemplateFile.mkdir(cutName+'_'+nuisance)
                    ptRelTemplateFile.mkdir(cutName+'_'+nuisance+'/ptrel')
                    ptRelTemplateFile.cd(cutName+'_'+nuisance+'/ptrel')

                    for sample in sampleCutName:

                        if '_'.join([ 'histo', sample, nuisance ]) in list(outputTemplates[cutName+sampleCutName[sample]].keys()):

                            nuisanceHisto = copy.deepcopy(outputTemplates[cutName+sampleCutName[sample]]['_'.join([ 'histo', sample, nuisance ])])
                            nuisanceHisto.Write()
                            if opt.verbose: print('        ', cutName+'_'+nuisance, sampleCutName[sample], '_'.join([ 'histo', sample, nuisance ]), nuisanceHisto.GetName())

                            centralTemplate = copy.deepcopy(nuisanceHisto)
                            centralTemplate.SetName('histo_'+sample)
                            centralTemplate.SetTitle('histo_'+sample)
                            centralTemplate.Write()
                            if opt.verbose: print('        ', cutName+'_'+nuisance, sampleCutName[sample], '_'.join([ 'histo', sample, nuisance ]), centralTemplate.GetName())

                            nuisanceCorrections = [ 1. ]
                            originalCentralTemplate = copy.deepcopy(outputTemplates[cutName+sampleCutName[sample]]['histo_'+sample])
                            for ib in range(1, nuisanceHisto.GetNbinsX()+1): 
                                if originalCentralTemplate.GetBinContent(ib)>0.: nuisanceCorrections.append(nuisanceHisto.GetBinContent(ib)/originalCentralTemplate.GetBinContent(ib))
                                else: nuisanceCorrections.append(1.)

                            for template in list(outputTemplates[cutName+sampleCutName[sample]].keys()):                           
                                if template.split('_')[1]==sample and nuisance not in template and template!='histo_'+sample:
                                    templateCut = cutName+template.replace('histo_'+sample,'')+sampleCutName[sample]
                                    if templateCut in outputTemplates and '_'.join([ 'histo', sample, nuisance ]) in outputTemplates[templateCut]:
                                        templateHisto = copy.deepcopy(outputTemplates[templateCut]['_'.join([ 'histo', sample, nuisance ])])
                                        templateHisto.SetName(template)
                                        templateHisto.SetTitle(template)
                                        templateHisto.Write()
                                        if opt.verbose: print('        ', cutName+'_'+nuisance, templateCut, '_'.join([ 'histo', sample, nuisance ]), templateHisto.GetName())
                                    else:
                                        templateHisto = copy.deepcopy(outputTemplates[cutName+sampleCutName[sample]][template])
                                        correctionStatus = ''
                                        if nuisance.replace('Up','').replace('Down','') not in template:
                                            for ib in range(1, nuisanceHisto.GetNbinsX()+1):
                                                templateHisto.SetBinContent(ib, templateHisto.GetBinContent(ib)*nuisanceCorrections[ib])
                                            correctionStatus = 'corrected'
                                        templateHisto.Write()
                                        if opt.verbose: print('        ', cutName+'_'+nuisance, sampleCutName[sample], template, templateHisto.GetName(), correctionStatus) 

                        else:
                            for template in list(outputTemplates[cutName+sampleCutName[sample]].keys()):
                                if template.split('_')[1]==sample:
                                    templateHisto = copy.deepcopy(outputTemplates[cutName+sampleCutName[sample]][template])
                                    templateHisto.Write()
                                    if opt.verbose: print('        ', cutName+'_'+nuisance, sampleCutName[sample], template, templateHisto.GetName())  

                        if 'nuis' in templateTreatmentDict:
                            if sample in templateTreatmentDict['nuis']:

                                correctionFlag = '_Corr'+sample.replace('jets','').upper()
                                nuisanceFlag = '_'+nuisance if '_'.join([ 'histo', sample, nuisance ]) in list(outputTemplates[cutName+sampleCutName[sample]].keys()) else ''
                                nominalHisto = copy.deepcopy(outputTemplates[cutName]['histo_'+sample+nuisanceFlag])
                                correctedHisto = copy.deepcopy(outputTemplates[cutName+correctionFlag]['histo_'+sample+nuisanceFlag])

                                if sampleCutName[sample]=='':
                                    nominalHisto.SetName('histo_'+sample+correctionFlag+'Down')
                                    nominalHisto.SetTitle('histo_'+sample+correctionFlag+'Down')
                                    correctedHisto.SetName('histo_'+sample+correctionFlag+'Up')
                                    correctedHisto.SetTitle('histo_'+sample+correctionFlag+'Up')
                                else:
                                    nominalHisto.SetName('histo_'+sample+correctionFlag+'Up')
                                    nominalHisto.SetTitle('histo_'+sample+correctionFlag+'Up')
                                    correctedHisto.SetName('histo_'+sample+correctionFlag+'Down')
                                    correctedHisto.SetTitle('histo_'+sample+correctionFlag+'Down')

                                nominalHisto.Write()
                                correctedHisto.Write()
                                if opt.verbose: print('        ', cutName+'_'+nuisance, sampleCutName[sample], sample, correctionFlag, nominalHisto.GetName(), correctedHisto.GetName(), '->', cutName+'_'+nuisance) 

                    if opt.verbose: print('        ', 'done', cutName, nuisance, '\n')
                    doneNuisance.append(nuisance)

        if opt.verbose: print('\n\n')

def system8Input(opt): # TODO port to Run3 cuts/variables structure


    #You run this method with ./runAnalysis.py --action=shapesForFit --year=CAMPAIGNNAME --tag=System8Templates.mujetpt.mujeteta/PtRelTemplates.mujetpt.mujeteta
    #For example ./runAnalysis.py --action=shapesForFit --year=Summer22 --tag=System8Templates.mujetpt.mujeteta

    
    #input datafile are at: opt.shapedir/opt.year/System8Templates{typeOfSys}{VarUpOrDown}/Samples/plots_Summer22System8Templates{typeOfSys}{VarUpOrDown}_ALL_DATA.root
    # for example: Shapes/Summer22/System8TemplatesAwayJetUp/Samples/plots_Summer22System8TemplatesAwayJetUp_ALL_DATA.root

    #input mc files are at: opt.shapedir/opt.year/System8Templates{typeOfSys}{VarUpOrDown}.mujetpt.mujeteta/Samples/plots_Summer22System8TemplatesAwayJetDown.mujetpt.mujeteta_ALL_{bjets, light}.root
    # for example: Shapes/Summer22/System8TemplatesAwayJetDown.mujetpt.mujeteta/Samples/plots_Summer22System8TemplatesAwayJetDown.mujetpt.mujeteta_ALL_light.root
    


    fulltag = opt.tag.split('.')
    basetag = opt.tag.split('.')[0]
    suffixtag = ''#this is the mujetpt.mujeteta
    for i in range(1, len(fulltag)): suffixtag = suffixtag + '.' +  fulltag[i]
    #print "basetag=", basetag
    #print "suffixtag=", suffixtag


    
    samples, cuts, variables = commonTools.getDictionariesInLoop(opt, opt.year, opt.tag, opt.sigset, 'variables')


    #print "samples:"
    #for i in samples: print i
    #print "----------"
    #print "cuts (This is the folder):"
    #for i in cuts: print i
    #print "----------"
    #print "variables:"
    #for i in variables: print i
    #print "----------"
    
    # example of "variables":
    # ptrel_ParticleNetVVT
    # ptrel_ParTL
    # ptrel_DeepJetT
    # ptrel_ParTVT
    # ptrel_ParTT
    # ptrel_ParticleNetT
    # ptrel_ParTVVT
    # ptrel_DeepJetM
    # ptrel_DeepJetL
    # ptrel
    # ptrel_ParTM
    # ptrel_ParticleNetM
    # ptrel_ParticleNetL
    # ptrel_DeepJetVVT
    # ptrel_DeepJetVT
    # ptrel_ParticleNetVT






    outputDir = '/'.join([ './System8Input', opt.year, opt.tag.split('__')[0] ])
    os.system('mkdir -p '+outputDir)


    mapSyst = {'Central' : {''} , 'AwayJet': {'Up', 'Down'}, 'MuPt': {'Up', 'Down'}, 'MuDR': {'Up', 'Down'}, 'JEU': {'Up', 'Down'}}
    #if you only want to run Central:
    #mapSyst = {'Central' : {''}}

    mapDataset = {'DATA'   : { 'lepton_in_jet' : [ 'n_pT'   , 'ntag_pT'   , 'p_pT'   , 'ptag_pT'    ] },
                  'bjets'  : { 'MCTruth'       : [ 'n_pT_b' , 'ntag_pT_b' , 'p_pT_b' , 'ptag_pT_b'  ] },
                  'light'  : { 'MCTruth'       : [ 'n_pT_cl', 'ntag_pT_cl', 'p_pT_cl', 'ptag_pT_cl' ] } }

    ptEdges_Example = []
    ptRelRange_Example = []
    for syst in mapSyst:
        print ("  syst=", syst)
        syst_name = syst
        isCentral = False
        if 'Central' in syst:
            isCentral = True
            syst_name = ''
        ###print "    isCentral =",  isCentral
        for sysvar in mapSyst[syst]:
            ###print "      sysvar=", '_' + sysvar + '_'

            #define variable to book only the lepton_in_jet histograms for MC the first time we pass
            isSecondMC= False
            EnteredBjets = False
            EnteredLight = False

            for dataset_b_l_data in mapDataset.keys():#loop to DATA, bjets, and light
                if ('bjets' in dataset_b_l_data): EnteredBjets = True
                if ('light' in dataset_b_l_data): EnteredLight = True
                if EnteredBjets and EnteredLight: isSecondMC = True

                dataset_qcd_data = 'QCD'
                isDATA= False
                if 'DATA' in dataset_b_l_data:
                    isDATA = True
                    dataset_qcd_data = 'Data'

                print ("        the dataset is", dataset_b_l_data)
                dataset_suffix = dataset_b_l_data

                tag = basetag + syst_name + sysvar
                if not isDATA: tag = tag + suffixtag

                if 'JEU' in syst_name and isDATA:  tag = basetag 
                inputFile = commonTools.openSampleShapeFile(opt.shapedir, opt.year, tag, dataset_suffix)
                ###print "        -->inputFile name: ", inputFile.GetName()
                
                ###print "        number of elements in cuts =", len(cuts)                
                ###print "        number of elements in variables =", len(variables)                
                for i_variables in variables:
                    print ("          variables=", i_variables)
                    if len(i_variables.split('_')) == 2:
                        btagWP = i_variables.split('_')[1]
                        #print "          btagWP=", btagWP
                        outputFileName = '_'.join([ 'S8', dataset_qcd_data, syst + sysvar, btagWP, 'anyEta.root' ])
                        print ("          outputFileName=", outputFileName)


                        #First loop to cuts to define ptEdges
                        ptEdges = []
                        for ptbin in cuts:
                            if '_' not in ptbin: 
                                for binedge in [ float(ptbin.split('Pt')[1].split('to')[0]), float(ptbin.split('to')[1]) ]:
                                    if binedge not in ptEdges:
                                        ptEdges.append(binedge)
                        ptEdges.sort()
                        ###print "          ptEdges=", ptEdges
                        ptRelRange = variables['ptrel']['range']
                        ###print "          ptRelRange=", ptRelRange

                        #Vizan: I eliminated a layer of loops so I use a dummy loop with one iteration
                        #to avoid reindenting everything
                        #instead of looping to lepton_in_jet and MCTruth:
                        #  for data I book and fill the histograms under ['lepton_in_jet', selection] (example: ['lepton_in_jet', 'ntag_pT'])
                        #  for MC (bjets, or light):
                        #     I book the histograms and filled them under ['MCTruth', selection_b/cl] (example: ['lepton_in_jet', 'ntag_pT_b'])
                        #     I book the histograms only the first time (bjets or light) under ['lepton_in_jet', 'selection'] (example: ['lepton_in_jet', 'ntag_pT'])
                        #      and fill them in the corresponding iteration (bjets or light)
                        #     In a separate loop the histograms for bjets and light are added

                        for idummy in range(0, 1):
                            ###print "            isSecondMC", isSecondMC
                            #i_cuts has the structure: ptrange_{'AwayJetTag, ''}
                            #for example for Pt200to300 we have 'Pt200to300' and 'Pt200to300_AwayJetTag'
                    

                            if isDATA or (not isDATA and not isSecondMC): outputHistogram = {}


                            directory = ''
                            if isDATA: directory = 'lepton_in_jet'
                            else: directory = 'MCTruth'

                            outputHistogram[directory] = {}

                            #for bjets and light I also will fill at once the lepton_in_jet histos (they are combined later)
                            if not isDATA and not isSecondMC:
                                ###print "            initializing outputHistogram['lepton_in_jet']"
                                outputHistogram['lepton_in_jet'] = {}

                            for selection in mapDataset[dataset_b_l_data][directory]:#loopt to for example: 'n_pT'   , 'ntag_pT'   , 'p_pT'   , 'ptag_pT'

                                outputHistogram[directory][selection] = commonTools.bookHistogram(selection, [ ptEdges ], ptRelRange, selection)

                                selection_for_lepton_in_jet = ''
                                if dataset_qcd_data=='QCD':#bjets or light
                                    if 'bjets' in dataset_b_l_data: selection_for_lepton_in_jet = selection.replace('_b', '')
                                    if 'light' in dataset_b_l_data: selection_for_lepton_in_jet = selection.replace('_cl', '')
                                    if selection_for_lepton_in_jet != 'n_pT' and selection_for_lepton_in_jet != 'ntag_pT' and  selection_for_lepton_in_jet != 'p_pT' and selection_for_lepton_in_jet != 'ptag_pT':
                                        print ("ABORTING, UNKNOWN VALUE FOR selection_for_lepton_in_jet=", selection_for_lepton_in_jet)
                                        print ("selection was=", selection)
                                        return

                                #For MC book the lepton_in_jet only the first time we enter (either bjets or light)
                                if not isDATA and not isSecondMC: outputHistogram['lepton_in_jet'][selection_for_lepton_in_jet] = commonTools.bookHistogram(selection_for_lepton_in_jet, [ ptEdges ], ptRelRange, selection_for_lepton_in_jet)

                                #this should never happen anyway
                                if dataset_qcd_data=='QCD' and directory=='lepton_in_jet': continue


                                ###print "              selection=", selection
                                ###print "              sample=", dataset_b_l_data
 
                                for dir_ptrange_nORp in cuts:

                                    ptrange = dir_ptrange_nORp.split('_')[0]
                                    isAwayJet = False
                                    if 'AwayJetTag' in dir_ptrange_nORp.split('_')[-1]: isAwayJet = True

                                    ###print "               ptbin=", dir_ptrange_nORp, " isAwayJet=", isAwayJet,  "prtange= ", ptrange

                                    if not isAwayJet and 'p_' in selection: continue
                                    if not isAwayJet and 'ptag_' in selection: continue
                                    
                                    if isAwayJet and 'n_' in selection: continue
                                    if isAwayJet and 'ntag_' in selection: continue

                                    string_motherHisto = ''
                                            
                                    if 'n_' in selection or 'p_' in selection: string_motherHisto = '/'.join([ dir_ptrange_nORp, 'ptrel', 'histo_'+dataset_b_l_data ])
                                    elif 'ptag_' in selection or 'ntag_' in selection: string_motherHisto = '/'.join([ dir_ptrange_nORp, 'ptrel_' + btagWP, 'histo_'+dataset_b_l_data ])
                                    else:
                                        print ("we are in trouble cause I don't now which one is the motherHisto for selection=", selection)
                                        return

                                    ###print ("               string_motherHisto= ", string_motherHisto)

                                    motherHisto = inputFile.Get(string_motherHisto)
                                    ptValue = (float(ptrange.split('Pt')[1].split('to')[0])+float(ptrange.split('to')[1]))/2.
                                    ###print "               ptValue=", ptValue

                                    for ib in range(1, motherHisto.GetNbinsX()+1):

                                        ptRelValue = motherHisto.GetBinCenter(ib)
                                        bin2D = outputHistogram[directory][selection].FindBin(ptValue, ptRelValue) 
                                        ###if ib == 1: print ("               ib==1: outputHistogram[directory=", directory, "][selection=", selection, "]=", motherHisto.GetBinContent(ib), " bin2D=", bin2D)

                                        outputHistogram[directory][selection].SetBinContent(bin2D, motherHisto.GetBinContent(ib))
                                        outputHistogram[directory][selection].SetBinError(bin2D, motherHisto.GetBinError(ib)) 

                                #Vizan: Now I have finished all ptranges for a given region: for example n_tag
                                #outputHistogram already set for data (but with scaled to the number of events if there was no prescale) under ['lepton_in_jet', selection]
                                #outputHistogram already set for mc (bjets or light) under ['MCTruth', selection_b/cl]
                                
                                #Vizan: I set outputHistogram for mc (bjets or light) under ['lepton_in_jet', selection]
                                if dataset_qcd_data=='QCD':#bjets or light
                                    if dataset_b_l_data =='bjets':
                                        ###print "              filling lepton_in_jet for bjets"
                                        outputHistogram['lepton_in_jet'][selection_for_lepton_in_jet].Add(outputHistogram['MCTruth'][selection_for_lepton_in_jet+'_b'])
                                    if dataset_b_l_data =='light':
                                        ###print "              filling lepton_in_jet for light"
                                        outputHistogram['lepton_in_jet'][selection_for_lepton_in_jet].Add(outputHistogram['MCTruth'][selection_for_lepton_in_jet+'_cl'])



                                #Vizan: Only for data I remove the prescale to recover the actual number of data events
                                if isDATA:
                                    errorDataYields = ctypes.c_double()
                                    dataYields = outputHistogram['lepton_in_jet'][selection].IntegralAndError(-1, -1, -1, -1, errorDataYields)
                                    dataPS = pow(dataYields/errorDataYields.value, 2)/dataYields
                                    #print ("               for selection=", selection, "dataPS=", dataPS)
                                    outputHistogram['lepton_in_jet'][selection].Scale(dataPS)


                            #Vizan: for the second pass of MC (bjets or light) we update the file to write the histograms corresponding to the second flavor (either of _b or _cl)
                            file_option = 'recreate'
                            if not isDATA and isSecondMC: file_option = 'update'
                            outputFile = commonTools.openRootFile(outputDir+'/'+outputFileName, file_option)


                            if not isDATA and not isSecondMC: outputFile.mkdir(directory)#'MCTruth' directory
                            if isDATA: outputFile.mkdir(directory)#'lepton_in_jet' directory

                            outputFile.cd(directory) 

                            for selection in mapDataset[dataset_b_l_data][directory]:#loopt to for example: 'n_pT'   , 'ntag_pT'   , 'p_pT'   , 'ptag_pT'
                                outputHistogram[directory][selection].Write()



                            outputFile.cd()
                            outputFile.Write()
                            outputFile.Close()


            #Vizan: In this additional loop we pass first for WP and, then for (bjets or light). Instead of other way around
            # The goal is simply to produce the histograms in the 'lepton_in_jet' for S8_QCD*.root rootfiles 
            for i_variables in variables:

                if len(i_variables.split('_')) == 2:
                    btagWP = i_variables.split('_')[1]
                    outFileName = '_'.join([ 'S8', 'QCD', syst + sysvar, btagWP, 'anyEta.root' ])
                    outFile = commonTools.openRootFile(outputDir+'/'+outFileName, 'update')

                    #Vizan: this could be done a little more elegantly
                    outFile.mkdir('lepton_in_jet')
                    outFile.cd('lepton_in_jet')

                    
                    for selection in ("n_pT"   , "ntag_pT"   , "p_pT"   , "ptag_pT"):

                        h2b = outFile.Get("MCTruth/" + selection + "_b")
                        h2Sum = h2b.Clone()
                        h2Sum.Add(outFile.Get("MCTruth/" + selection + "_cl"))
                        h2Sum.Write(selection)



                    outFile.cd()
                    outFile.Write()
                    outFile.Close()
                                                        
def frameworkValidation(opt):

    if 'JEU' in opt.tag:
        print('frameworkValidation: JEU in PtRelTools not up-to-date, exiting')
        exit()

    if 'Light' in opt.tag and 'Merged' not in opt.tag:
        mergeLightShapes(opt)
        opt.tag = opt.tag.replace('Light', 'MergedLight')

    ptRelToolsDir = '/afs/cern.ch/work/s/scodella/BTagging/CMSSW_10_6_28/src/PlotsConfigurations/Configurations/Analysis/PtRelTools/Templates/Histograms/'

    histoToCompare = { 'LightKinematics'   : { 'jetpt'         : [ 'jetPt_DATASET_PTTBIN_anyEta_TRIGGER_SELECTION',                    'PTBIN/lightjetpt_PTBIN/histo_SAMPLE'       ] },
                       'PtRelKinematics'   : { 'jetpt'         : [ 'jetPt_DATASET_PTTBIN_anyEta_TRIGGER_SELECTION',                    'PTBIN/mujetpt_PTBIN/histo_SAMPLE'          ] },
                       'System8Kinematics' : { 'jetpt'         : [ 'jetPt_DATASET_PTTBIN_anyEta_TRIGGER_SELECTION',                    'PTBIN/mujetpt_PTBIN/histo_SAMPLE'          ] },
                       'LightTemplates'    : { 'ptrel'         : [ 'PtRel_DATASET_PTTBIN_anyEta_TRIGGER_SELECTION_DeepJetM_Untag_trk', 'PTBIN/ptrel_PTBIN/histo_SAMPLE'            ] },
                       'PtRelTemplates'    : { 'ptrelpass'     : [ 'PtRel_DATASET_PTTBIN_anyEta_TRIGGER_SELECTION_TAGWP_TagFLAVOUR',   'PTBIN/ptrel_TAGWP_Pass/histo_SAMPLE'       ],
                                               'ptrelfail'     : [ 'PtRel_DATASET_PTTBIN_anyEta_TRIGGER_SELECTION_TAGWP_UntagFLAVOUR', 'PTBIN/ptrel_TAGWP_Fail/histo_SAMPLE'       ] },
                       'System8Templates'  : { 'ptrel'         : [ 'n_pT_PTTBIN_anyEta_TRIGGER_SELECTIONFLAVOUR',                      'PTBIN/ptrel/histo_SAMPLE'                  ],
                                               'ptrelpass'     : [ 'ntag_pT_PTTBIN_anyEta_TRIGGER_SELECTION_TAGWPFLAVOUR',             'PTBIN/ptrel_TAGWP/histo_SAMPLE'            ],
                                               'ptrelaway'     : [ 'p_pT_PTTBIN_anyEta_TRIGGER_SELECTIONFLAVOUR',                      'PTBIN_AwayJetTag/ptrel/histo_SAMPLE'       ],
                                               'ptrelawaypass' : [ 'ptag_pT_PTTBIN_anyEta_TRIGGER_SELECTION_TAGWPFLAVOUR',             'PTBIN_AwayJetTag/ptrel_TAGWP/histo_SAMPLE' ] } }

    keyTag = ''
    for key in histoToCompare:
        if key in opt.tag: keyTag = key
    if keyTag=='': 
        print('frameworkValidation: invalid keyTag, exiting')
        exit()

    selection = 'Central'
    for sel in opt.Selections:
        if sel in opt.tag: 
            if sel=='AwayJetUp': selection = 'JBPT'
            elif sel=='AwayJetDown': selection = 'JBPL'
            elif sel=='MuPtUp': selection = 'MuPt8'
            elif sel=='MuPtDown': selection = 'MuPt6'
            elif sel=='MuDRUp': selection = 'MuDRPlus'
            elif sel=='MuDRDown': selection = 'MuDRMinus'

    for sample in opt.samples:

        if sample=='JetMET': 
            ptRelToolsFileName = 'PtRel_LightHistograms_Run2022FG_LowPtAwayTrgConf.root'
            dataset = 'JetHT'
        elif sample=='QCD': 
            ptRelToolsFileName = 'PtRel_LightHistograms_PT-80to120_LowPtAwayTrgConf.root'
            dataset = 'QCD'
        elif 'PtRel' in opt.tag:
            if sample=='DATA': 
                ptRelToolsFileName = 'PtRel_Histograms_BTagMu_Run2022FG_LowPtAwayTrgConf.root'
                dataset = 'BTagMu'
            else:
                ptRelToolsFileName = 'PtRel_Histograms_QCDMu_PT-80to120_LowPtAwayTrgConf.root'
                dataset = 'QCDMu'
        elif 'System8' in opt.tag:
            if sample=='DATA':  
                ptRelToolsFileName = 'System8_Histograms_Run2022FG_LowPtAway.root'
                dataset = 'BTagMu'
            else: 
                ptRelToolsFileName = 'System8_Histograms_PT-80to120_LowPtAway.root'
                dataset = 'QCDMu'

        inputFile = [ commonTools.openRootFile(ptRelToolsDir+ptRelToolsFileName), commonTools.openSampleShapeFile(opt.shapedir, opt.year, opt.tag, sample) ]

        flavour = ''
        if sample=='light': flavour = '_cl'
        elif sample=='ljets': flavour = '_lg'
        elif 'jets' in sample: flavour = '_'+sample.replace('jets','')

        for ptbin in opt.ptBins:
            
            for tr in opt.triggerInfos:
                if float(ptbin.split('Pt')[1].split('to')[0])<float(opt.triggerInfos[tr]['jetPtRange'][1]) and float(opt.triggerInfos[tr]['jetPtRange'][0])<float(ptbin.split('to')[1]):
                    trigger = tr.replace('BTagMu_AK4','').replace('_Mu5','')                  

            for histokey in histoToCompare[keyTag]:

                btagWPList = opt.btagWPs if 'pass' in histokey or 'fail' in histokey else [ '' ] 
                for wp in btagWPList:
                    if 'VT' in wp or 'VVT' in wp or 'JBPT' in wp: continue 

                    histos = []
                    for his in range(2):
                        histoName = histoToCompare[keyTag][histokey][his].replace('DATASET',dataset).replace('PTTBIN',ptbin.replace('to','')).replace('TRIGGER',trigger).replace('SELECTION',selection).replace('FLAVOUR',flavour).replace('PTBIN',ptbin).replace('SAMPLE',sample).replace('TAGWP',wp).replace('10001400','1000')
                        histos.append(inputFile[his].Get(histoName))

                    if histos[0].GetEntries()==0.: continue

                    if sample!='DATA' and sample!='JetMET':
                        weight0 = 0.39821973443 if 'LightTemplates' in opt.tag else histos[0].Integral(-1,-1)/histos[0].GetEntries()
                        histos[0].Scale(1./weight0)

                    lastBin0 = histos[0].GetBinContent(histos[0].GetNbinsX())+histos[0].GetBinContent(histos[0].GetNbinsX()+1)
                    histos[0].SetBinContent(histos[0].GetNbinsX(), lastBin0)

                    if abs(histos[1].Integral()/histos[0].Integral()-1.)>0.00003 or opt.verbose:
                        print('Events', sample, ptbin, histokey, wp, histos[0].Integral(), histos[1].Integral(), histos[1].Integral()/histos[0].Integral()-1.)

                    if 'events' in opt.option: continue
 
                    if 'jetpt' not in histokey and histos[0].GetNbinsX()!=histos[1].GetNbinsX():
                        if histos[0].GetNbinsX()>histos[1].GetNbinsX():
                            rbin = float(histos[0].GetNbinsX())/float(histos[1].GetNbinsX())
                            if rbin==int(rbin): histos[0].Rebin(int(rbin))
                            elif opt.verbose: 
                                print('Binning not comparable:', ptbin, histokey, wp, histos[0].GetNbinsX(), histos[1].GetNbinsX())
                                continue
                        elif histos[1].GetNbinsX()>histos[0].GetNbinsX():
                            rbin = float(histos[1].GetNbinsX())/float(histos[0].GetNbinsX())
                            if rbin==int(rbin): histos[1].Rebin(int(rbin))
                            elif opt.verbose: 
                                print('Binning not comparable:', ptbin, histokey, wp, histos[0].GetNbinsX(), histos[1].GetNbinsX())
                                continue

                    binoffset = int(ptbin.split('Pt')[1].split('to')[0]) if 'jetpt' in histokey else 0

                    for ib in range(1, histos[1].GetNbinsX()+1):
                        if histos[0].GetBinContent(ib+binoffset)>0.:
                            if abs(histos[1].GetBinContent(ib)/histos[0].GetBinContent(ib+binoffset)-1.)>0.00003 and (opt.verbose or abs(histos[1].GetBinContent(ib)-histos[0].GetBinContent(ib+binoffset))>1):
                                print('Shapes', sample, ptbin, histokey, wp, histos[1].GetBinLowEdge(ib), histos[0].GetBinContent(ib+binoffset), histos[1].GetBinContent(ib), histos[1].GetBinContent(ib)/histos[0].GetBinContent(ib+binoffset)-1.)

### Prefit plots

def plotKinematics(opt):

    if not commonTools.foundShapeFiles(opt, True, False) or opt.reset:
        if '.' in opt.tag:
            os.system('cp '+commonTools.getSampleShapeFileName(opt.shapedir, opt.year, opt.tag.split('.')[0], 'DATA')+' '+commonTools.getSampleShapeFileName(opt.shapedir, opt.year, opt.tag, 'DATA'))
        latinoTools.mergeall(opt) 

    latinoTools.plots(opt)

def plotTemplates(opt):

    bTagPerfAnalysis(opt, 'prefitplots')

### Fits and postfit plots

def bTagPerfAnalysis(opt, action):

    commonTools.getConfigParameters(opt, [ 'systematicVariations', 'jetPtBins', 'bTagWorkingPoints' ]) 

    splitJetPtBins = [ 'all' ] if '_mergedJetPtBins' in opt.tag else list(opt.jetPtBins.keys())
    splitSelections = [ 'all' ] if '_mergedSelections' in opt.tag else opt.systematicVariations
    mergedSelectionFlag = '_mergedSelections_nuisSelections' if '_nuisSelections' in opt.tag else '_mergedSelections'

    for btagWP in list(opt.bTagWorkingPoints.keys()):
        fitTagList = []
        for ptbin in splitJetPtBins:
            for selection in splitSelections:
                sel = 'Central' if selection=='' else selection

                tagOptionList = [ opt.tag.split('___')[0], '_btag'+btagWP ]
                if ptbin=='all': tagOptionList.append('__mergedJetPtBins')
                else: tagOptionList.append('__Jet'+ptbin)
                if sel=='all': tagOptionList.append(mergedSelectionFlag)
                else: tagOptionList.append('_sel'+sel)

                optAux = copy.deepcopy(opt)
                optAux.tag = '_'.join(tagOptionList)

                fitTagList.append(optAux.tag.replace('__sel','____sel'))

                if action=='prefitplots': latinoTools.plots(optAux)
                elif action=='datacards': combineTools.writeDatacards(optAux)
                elif action=='ptrelfit': 
                    if len(fitTagList)==len(splitJetPtBins)*len(splitSelections):      
                        optAux.tag = '-'.join(fitTagList)
                        combineTools.mlfits(optAux)
                elif action=='system8fit': runSystem8Fit(optAux)
                elif action=='getbtagperffitresults': getBTagPerfFitResults(optAux, opt)
                elif 'prefit' in action or 'postfit' in action:
                    if commonTools.isGoodFile(commonTools.getCombineOutputFileName(optAux, '', '', optAux.tag, 'mlfits'), 6000.):
                        if action=='prefitplots': latinoTools.postFitPlots(optAux)
                        elif commonTools.goodCombineFit(optAux, optAux.year, optAux.tag, '', 'PostFitS'):  
                            if action=='postfitshapes':  latinoTools.postFitShapes(optAux) 
                            elif action=='postfitplots': latinoTools.postFitPlots(optAux)
                        elif opt.verbose: print('Warning: failed fit for campaign='+optAux.year+', WP='+btagWP+', bin='+ptbin)
                    elif opt.verbose: print('Warning: input ML fit file', commonTools.getCombineOutputFileName(optAux), '', '', optAux.tag, 'mlfits', 'not found') 
                elif action=='checkfit': 
                    if not commonTools.isGoodFile(commonTools.getCombineOutputFileName(opt, '', '', opt.tag, 'mlfits'), 6000.):
                        print('Input ML fit file', commonTools.getCombineOutputFileName(opt, '', '', opt.tag, 'mlfits'), 'not found')
                    elif not commonTools.goodCombineFit(opt, optAux.year, optAux.tag, '', 'PostFitS'):
                        print('Failed fit for campaign='+optAux.year+', WP='+btagWP+', bin='+ptbin)

def ptRelDatacards(opt):

    bTagPerfAnalysis(opt, 'datacards')
 
def ptRelFits(opt):

    opt.batchQueue = 'workday' if '_merged' in opt.tag else 'longlunch'
    opt.option += 'skipbonly'
    bTagPerfAnalysis(opt, 'ptrelfit')

def ptRelFitCheck(opt):

    bTagPerfAnalysis(opt, 'checkfit')

def ptRelPreFitPlots(opt):

    opt.option += 'prefit'
    bTagPerfAnalysis(opt, 'prefitplots')

def ptRelPostFitShapes(opt):

    opt.option += 'postfits'
    bTagPerfAnalysis(opt, 'postfitshapes')

def ptRelPostFitPlots(opt):

    opt.option += 'postfits'
    bTagPerfAnalysis(opt, 'postfitplots')

def system8Fits(opt):

    bTagPerfAnalysis(opt, 'system8fit')

def runSystem8Fit(opt):

    print('please, write me if useful')

### Efficiencies and scale factors

def readOldPtRelFitResultsFromTables(opt, btagWP, ptbin, systematic):

    efficiencyMC, uncertaintyMC, efficiencyFit, uncertaintyFit, scaleFactor, scaleFactorUncertainty = -1., -1., -1., -1., -1., -1.

    tableName = '/afs/cern.ch/work/s/scodella/BTagging/CodeDevelopment/CMSSW_10_2_11/src/RecoBTag/PerformanceMeasurements/test/PtRelTools/Tables/PtRelFit_'+btagWP+'_anyEta_'+ptbin.replace('to','')+'_'+systematic+'_PSRun2017UL17_KinEtaAfterPtBinsCentral_LowPtAwayTrgConf_Run2016Production.txt'

    tableFile = open(tableName, 'r')
    lines = tableFile.readlines()
    for line in lines:
        if 'Efficiency MC' in line:
            efficiencyMC  = float(line.split(' = ')[1].split(' +/- ')[0])
            uncertaintyMC = float(line.split(' +/- ')[1].split('\n')[0])
        elif 'Eff. data' in line:
            efficiencyFit  = float(line.split(' = ')[1].split(' +/- ')[0])
            uncertaintyFit = float(line.split(' +/- ')[1].split(' (')[0])
        elif 'Scale factor' in line:
            scaleFactor = float(line.split(' = ')[1].split(' +/- ')[0])
            scaleFactorUncertainty = float(line.split(' +/- ')[1].split('\n')[0])

    return efficiencyMC, uncertaintyMC, efficiencyFit, uncertaintyFit, scaleFactor, scaleFactorUncertainty

def efficiencyError(P, F, eP, eF, correlation):

    T = P + F
    dP = (1./T -P/pow(T,2))
    dF = (-P/pow(T,2))

    return math.sqrt( pow(eP*dP,2) + pow(eF*dF,2) + 2.*correlation*eP*dP*eF*dF )

def getPtRelEfficiency(opt, inputFile, fileType, btagWP, ptbin, systematic):

    cut = '_'.join([ ptbin, btagWP, 'BTAGSTATUS', systematic ]).replace('_Central','')

    if fileType=='shapes': histoPath = cut+'/ptrel/histo_bjets'
    else: histoPath = 'shapes_fit_s/'+cut+'/total_signal'

    histoPass = inputFile.Get(histoPath.replace('BTAGSTATUS','Pass'))
    histoFail = inputFile.Get(histoPath.replace('BTAGSTATUS','Fail'))

    errorPassYield, errorFailYield = ctypes.c_double(), ctypes.c_double()
    passYield = histoPass.IntegralAndError(-1,-1,errorPassYield)
    failYield = histoFail.IntegralAndError(-1,-1,errorFailYield)

    if opt.verbose and fileType=='fit' and (errorPassYield.value==0. or errorFailYield.value==0.): 
        print('    Warning: missing erros in ML fit for', btagWP, ptbin, systematic)

    efficiency = passYield/(passYield+failYield)

    correlation = 0.

    if fileType!='shapes': # Use a trick for the time being
        histoTotal = inputFile.Get('shapes_fit_s/total_signal')
        errorTotalYield = ctypes.c_double()
        totalYield = histoTotal.IntegralAndError(-1,-1,errorTotalYield)

        if errorPassYield.value*errorFailYield.value!=0:
            correlation = (pow(errorTotalYield.value,2)-pow(errorPassYield.value,2)-pow(errorFailYield.value,2))/(2*errorPassYield.value*errorFailYield.value)

    return efficiency, efficiencyError(passYield, failYield, errorPassYield.value, errorFailYield.value, correlation), passYield+failYield

def getPtRelFitResults(opt, btagWP, ptbin, systematic):

    if commonTools.isGoodFile(commonTools.getCombineOutputFileName(opt, '', '', opt.tag, 'mlfits'), 6000.):
        if commonTools.goodCombineFit(opt, opt.year, opt.tag, '', 'PostFitS'):

            motherFile = commonTools.openShapeFile(opt.shapedir, opt.year, opt.tag.split('_')[0], 'SM', 'SM')
            fitFile = commonTools.openCombineFitFile(opt, '', opt.year, opt.tag)

            efficiencyMC,  uncertaintyMC,  yieldsMC  = getPtRelEfficiency(opt, motherFile, 'shapes', btagWP, ptbin, systematic)
            efficiencyFit, uncertaintyFit, yieldsFit = getPtRelEfficiency(opt, fitFile,    'fit',    btagWP, ptbin, systematic)

            if (efficiencyFit>0.999 and efficiencyFit/efficiencyMC>1.1) or (efficiencyFit>0.99 and efficiencyFit/efficiencyMC>1.1) or (efficiencyFit>0.98 and efficiencyFit/efficiencyMC>1.5):
                efficiencyFit, uncertaintyFit = 0.01, math.sqrt(efficiencyMC*(1.-efficiencyMC)/yieldsFit)
            elif uncertaintyFit==0.:
                uncertaintyFit = math.sqrt(efficiencyFit*(1.-efficiencyFit)/yieldsFit)

            scaleFactor = efficiencyFit/efficiencyMC
            scaleFactorUncertainty = scaleFactor*math.sqrt(pow(uncertaintyFit/efficiencyFit,2)+pow(uncertaintyMC/efficiencyMC,2))

            motherFile.Close()
            fitFile.Close()

            return efficiencyMC, uncertaintyMC, efficiencyFit, uncertaintyFit, scaleFactor, scaleFactorUncertainty

        elif opt.verbose: '  Warning: failed fit for campaign='+opt.year+', WP='+btagWP+', bin='+ptbin
    elif opt.verbose: print('Warning: input ML fit file', commonTools.getCombineOutputFileName(opt, '', '', opt.tag, 'mlfits'), 'not found')

    return -1., -1., -1., -1., -1., -1.

def getSystem8FitResults(opt, btagWP, ptbin, systematic):

    print('Please, write me if useful')

def getBTagPerfFitResults(opt, optOrig):

    btagWP = opt.tag.split('_btag')[1].split('_')[0] 
    ptbinList = [ 'Pt'+opt.tag.split('_JetPt')[1].split('_')[0] ] if '_JetPt' in opt.tag else opt.ptBins 
    systematicList = [ opt.tag.split('_sel')[1].split('_')[0] ] if '_sel' in opt.tag else opt.Selections

    if btagWP not in optOrig.bTagPerfResults: optOrig.bTagPerfResults[btagWP] = {}
  
    for syst in systematicList:
        systematic = 'Central' if syst=='' else syst
        if systematic not in optOrig.bTagPerfResults[btagWP]: optOrig.bTagPerfResults[btagWP][systematic] = {}
        for ptbin in ptbinList :
            optOrig.bTagPerfResults[btagWP][systematic][ptbin] = {}

            if 'ptreltools' in opt.option.lower():
                efficiencyMC, uncertaintyMC, efficiencyFit, uncertaintyFit, scaleFactor, scaleFactorUncertainty = readOldPtRelFitResultsFromTables(opt, btagWP, ptbin, systematic)

            elif opt.method=='PtRel':
                efficiencyMC, uncertaintyMC, efficiencyFit, uncertaintyFit, scaleFactor, scaleFactorUncertainty = getPtRelFitResults(opt, btagWP, ptbin, systematic)

            elif opt.method=='System8':
                efficiencyMC, uncertaintyMC, efficiencyFit, uncertaintyFit, scaleFactor, scaleFactorUncertainty = getSystem8FitResults(opt, btagWP, ptbin, systematic)

            optOrig.bTagPerfResults[btagWP][systematic][ptbin] = {}
            optOrig.bTagPerfResults[btagWP][systematic][ptbin]['efficiencyMC']             = efficiencyMC
            optOrig.bTagPerfResults[btagWP][systematic][ptbin]['efficiencyMCUncertainty']  = uncertaintyMC
            optOrig.bTagPerfResults[btagWP][systematic][ptbin]['efficiencyFit']            = efficiencyFit
            optOrig.bTagPerfResults[btagWP][systematic][ptbin]['efficiencyFitUncertainty'] = uncertaintyFit
            optOrig.bTagPerfResults[btagWP][systematic][ptbin]['scaleFactor']              = scaleFactor
            optOrig.bTagPerfResults[btagWP][systematic][ptbin]['scaleFactorUncertainty']   = scaleFactorUncertainty

def getBTagPerfResults(opt):

    opt.bTagPerfResults = {}
    bTagPerfAnalysis(opt, 'getbtagperffitresults')

### Plots for efficiencies and scale factors

def templateHistogram(opt, result):

    ptEdges = []
    for ptbin in opt.ptBins:
        for binedge in [ float(ptbin.split('Pt')[1].split('to')[0]), float(ptbin.split('to')[1]) ]:
            if binedge not in ptEdges:
                ptEdges.append(binedge)

    ptEdges.sort()

    return commonTools.bookHistogram(result, [ ptEdges ], style='')

def fillBTagPerfHistogram(opt, result, btagWP, bTagPerfSystematicResults):

    bTagPerfHisto = templateHistogram(opt, result)
    bTagPerfHisto.SetDirectory(0)

    for ptbin in bTagPerfSystematicResults:

        ib = bTagPerfHisto.FindBin((float(ptbin.split('Pt')[1].split('to')[0])+float(ptbin.split('to')[1]))/2.)
        bTagPerfHisto.SetBinContent(ib, bTagPerfSystematicResults[ptbin][result])
        bTagPerfHisto.SetBinError(ib, bTagPerfSystematicResults[ptbin][result+'Uncertainty'])

    bTagPerfHisto.SetXTitle('#mu-jet #font[50]{p}_{T} [GeV]')
    bTagPerfHisto.GetXaxis().SetRangeUser(opt.minPlotPt, opt.maxPlotPt)

    if 'efficiency' in result: 
        bTagPerfHisto.SetYTitle('b-tag Efficiency #epsilon_{b}')
        bTagPerfHisto.SetMinimum(0.4)
        bTagPerfHisto.SetMaximum(1.1)
    else: 
        bTagPerfHisto.SetYTitle(btagWP+' Data/Sim. SF_{b}')
        bTagPerfHisto.SetMinimum(0.6)
        bTagPerfHisto.SetMaximum(1.4)

    return bTagPerfHisto

def makeBTagPerformancePlot(opt, btagWP, bTagPerfHistos, resultToPlot):

    ySize, ylow = 800, 0.52
 
    if resultToPlot!='performance':
        ySize, ylow = 400, 0.03

    canvas = commonTools.bookCanvas('canvas', 1200, ySize)
    canvas.cd()

    pad = []
    pad.append(commonTools.bookPad('pad0', 0.02, ylow, 0.98, 0.98))
    if opt.maxPlotPt>=300.: pad[0].SetLogx()
    pad[0].Draw()

    if resultToPlot=='performance': 
        pad.append(commonTools.bookPad('pad1', 0.02, 0.03, 0.98, 0.49))
        if opt.maxPlotPt>=300.: pad[1].SetLogx()
        pad[1].Draw()

    for result in [ 'efficiency', 'scalefactor' ]:
        if result==resultToPlot or resultToPlot=='performance':

            if result=='scalefactor' and resultToPlot=='performance': pad[1].cd()
            else: pad[0].cd()

            legend = ROOT.TLegend(0.20,0.73,0.63,0.91);
            legend.SetHeader(btagWP) 
            legend.SetLineColor(0)
            legend.SetShadowColor(0)

            drawOption = 'p'
            markerColor =  1
            for tag in bTagPerfHistos:
                markerStyle = 20
                for systematic in opt.Selections: #bTagPerfHistos[tag]: # So the order is respected
                    styleOffset = 0
                    for btaghisto in [ 'efficiencyFit', 'efficiencyMC', 'scaleFactor' ]:
                        if result in btaghisto.lower():

                            if systematic=='FinalSystematics': 
                                bTagPerfHistos[tag][systematic][btaghisto].SetFillStyle(3005)
                                bTagPerfHistos[tag][systematic][btaghisto].SetFillColor(2)
                                drawOption = 'pe2'

                            if systematic=='Final':
                                legend.AddEntry(bTagPerfHistos[tag][systematic][btaghisto], 'Scale factors', 'p')
                                legend.AddEntry(bTagPerfHistos[tag][systematic+'Systematics'][btaghisto], 'Scale factor uncertainty', 'f')

                            bTagPerfHistos[tag][systematic][btaghisto].SetMarkerStyle(markerStyle+styleOffset)
                            bTagPerfHistos[tag][systematic][btaghisto].SetMarkerColor(markerColor)  
                            bTagPerfHistos[tag][systematic][btaghisto].Draw(drawOption)
                            drawOption = 'psame'
                            styleOffset = 4

                    if systematic!='FinalSystematics':
                        markerStyle += 1
                        markerColor += 1

            legend.Draw()

    tagFlag = '-'.join(list(bTagPerfHistos.keys()))
    if 'DepOn' in opt.option or 'Final' in opt.option:
        systematicFlag = opt.option
    else: 
        systematicFlag = '-'.join(list(bTagPerfHistos[list(bTagPerfHistos.keys())[0]].keys()))

    outputDir = '/'.join([ opt.plotsdir, opt.year, opt.method+'Results', tagFlag, resultToPlot ]) 
    os.system('mkdir -p '+outputDir+' ; cp ../../index.php '+opt.plotsdir)
    commonTools.copyIndexForPlots(opt.plotsdir, outputDir)

    canvas.Print(outputDir+'/'+btagWP+'_'+systematicFlag+opt.fitOption+'.png')

def computeFinalScaleFactors(opt):

    systematics, selections = [], []
    for systematic in opt.Selections:
        if systematic!='' and 'Down' not in systematic: 
            systematics.append(systematic.replace('Up',''))
            if systematic.replace('Up','') not in opt.systematicNuisances: selections.append(systematic.replace('Up',''))

    for btagWP in opt.btagWPs:

        wpSF = copy.deepcopy(opt.bTagPerfResults[btagWP])
        opt.bTagPerfResults[btagWP]['Final'] = {}
        opt.bTagPerfResults[btagWP]['StatisticsUp'] = {}
        opt.bTagPerfResults[btagWP]['StatisticsDown'] = {}
        opt.bTagPerfResults[btagWP]['FinalSystematics'] = {}
        opt.bTagPerfResults[btagWP]['FinalUp'] = {}
        opt.bTagPerfResults[btagWP]['FinalDown'] = {}

        for ptbin in opt.ptBins:

            centralSF = wpSF['Central'][ptbin]['scaleFactor']
            centralSFerror = wpSF['Central'][ptbin]['scaleFactorUncertainty']

            systSF, systSFerror = {}, {}
            for systematic in systematics:
                if systematic+'Up' in opt.Selections:
                    systSF[systematic], systSFerror[systematic] = {}, {}
                    sfUp, sfDown = 'Up', 'Down'
                    if wpSF[systematic+'Up'][ptbin]['scaleFactor']<wpSF[systematic+'Down'][ptbin]['scaleFactor']:
                        sfUp, sfDown = 'Down', 'Up'
                    systSF[systematic]['Up'] = wpSF[systematic+sfUp][ptbin]['scaleFactor']
                    systSF[systematic]['Down'] = wpSF[systematic+sfDown][ptbin]['scaleFactor']
                    systSFerror[systematic]['Up'] = wpSF[systematic+sfUp][ptbin]['scaleFactorUncertainty']
                    systSFerror[systematic]['Down'] = wpSF[systematic+sfDown][ptbin]['scaleFactorUncertainty']

            goodCentral = False

            if centralSF>0.1 and wpSF['Central'][ptbin]['efficiencyFit']>0.01:
                for systematic in selections:
                    if systematic+'Up' in opt.Selections:
                        if centralSF>=systSF[systematic]['Down'] and centralSF<=systSF[systematic]['Up']:
                            goodCentral = True
            
            if goodCentral: finalScaleFactor, finalScaleFactorUncertainty = centralSF, centralSFerror
            else: 
               
                finalScaleFactor, finalScaleFactorUncertainty, scaleFactorSystematicUncertainty = -1., -1., -1.

                scaleFactorList, scaleFactorUncertaintyList = [], []
                for systematic in list(wpSF.keys()):
                    if systematic=='Central' or systematic.replace('Up','').replace('Down','') in selections:
                        if wpSF[systematic][ptbin]['scaleFactor']>0.1 and wpSF[systematic][ptbin]['efficiencyFit']>0.01: 
                            scaleFactorList.append(wpSF[systematic][ptbin]['scaleFactor'])
                            scaleFactorUncertaintyList.append(wpSF[systematic][ptbin]['scaleFactorUncertainty'])

                hasOutliers = True
                while len(scaleFactorList)>0 and hasOutliers:
                    
                    finalScaleFactor = sum(scaleFactorList)/len(scaleFactorList)
                    finalScaleFactorUncertainty = sum(scaleFactorUncertaintyList)/len(scaleFactorUncertaintyList)
                    standardDeviaton = 0.
                    for sfValue in scaleFactorList: standardDeviaton += pow(sfValue-finalScaleFactor, 2)
                    standardDeviaton = math.sqrt(standardDeviaton/len(scaleFactorList))

                    scaleFactorToRemove = []
                    for sfValue in scaleFactorList:
                        if abs(sfValue-finalScaleFactor)>2.*standardDeviaton: scaleFactorToRemove.append(sfValue)
                    for sfValue in scaleFactorToRemove: 
                        scaleFactorList.remove(sfValue)
                    hasOutliers = len(scaleFactorToRemove)>0

            if finalScaleFactor>0.: 

                if opt.verbose: print('####', btagWP, ptbin)

                scaleFactorSystematicUncertainty = pow(finalScaleFactorUncertainty,2)    

                for systematic in systematics:

                    systematicVariations = {}

                    for variation in [ '', 'Up', 'Down' ]:
                        if systematic+variation in wpSF:
                            if wpSF[systematic+variation][ptbin]['scaleFactor']>0.1 and wpSF[systematic+variation][ptbin]['efficiencyFit']>0.01:
                                if wpSF[systematic+variation][ptbin]['scaleFactorUncertainty']<0.1 and abs(wpSF[systematic+variation][ptbin]['scaleFactor']-finalScaleFactor)<0.2:
                                    systematicVariations[variation] = wpSF[systematic+variation][ptbin]['scaleFactor']-finalScaleFactor

                    if len(list(systematicVariations.keys()))==2:
                        if max(abs(systematicVariations['Up']),abs(systematicVariations['Down']))>0.1:
                            if systematic in opt.systematicNuisances and min(abs(systematicVariations['Up']),abs(systematicVariations['Down']))>0.1:
                                for variation in [ 'Up', 'Down' ]:
                                    systematicVariations[variation] = wpSF[systematic+variation][ptbin]['scaleFactor']-centralSF
                            if min(abs(systematicVariations['Up']),abs(systematicVariations['Down']))>0.02:
                                if abs(systematicVariations['Up'])>abs(systematicVariations['Down']): del systematicVariations['Up']
                                else: del systematicVariations['Down']

                    if len(list(systematicVariations.keys()))==0: 
                        systematicUncertainty = 0.05*finalScaleFactor # Bho?
                    elif len(list(systematicVariations.keys()))==1: 
                        for variation in list(systematicVariations.keys()):
                             systematicUncertainty = systematicVariations[variation] if variation!='Down' else -systematicVariations[variation]
                    else: 
                        systematicUncertainty = (abs(systematicVariations['Up'])+abs(systematicVariations['Down']))/2.
                        if systematicVariations['Up']*systematicVariations['Down']<0.: systematicUncertainty = math.copysign(systematicUncertainty, systematicVariations['Up'])
                        elif abs(systematicVariations['Up'])>=abs(systematicVariations['Down']): systematicUncertainty = math.copysign(systematicUncertainty, systematicVariations['Up'])
                        else: systematicUncertainty = math.copysign(systematicUncertainty, -systematicVariations['Up'])

                    for variation in ['Up', 'Down' ]: 
                        if systematic+variation not in opt.bTagPerfResults[btagWP]:
                            opt.bTagPerfResults[btagWP][systematic+variation] = {}
                        if ptbin not in opt.bTagPerfResults[btagWP][systematic+variation]:
                            opt.bTagPerfResults[btagWP][systematic+variation][ptbin] = {} 

                    if opt.verbose: print('    ', systematic, systematicUncertainty)

                    opt.bTagPerfResults[btagWP][systematic+'Up'][ptbin]['scaleFactor'] = finalScaleFactor + systematicUncertainty
                    opt.bTagPerfResults[btagWP][systematic+'Down'][ptbin]['scaleFactor'] = finalScaleFactor - systematicUncertainty
                              
                    scaleFactorSystematicUncertainty += pow(systematicUncertainty,2)

                scaleFactorSystematicUncertainty = math.sqrt(scaleFactorSystematicUncertainty)

                if opt.verbose: print('     Total', scaleFactorSystematicUncertainty, '\n\n')    

            opt.bTagPerfResults[btagWP]['Final'][ptbin] = {}
            opt.bTagPerfResults[btagWP]['Final'][ptbin]['scaleFactor'] = finalScaleFactor
            opt.bTagPerfResults[btagWP]['Final'][ptbin]['scaleFactorUncertainty'] = finalScaleFactorUncertainty
            opt.bTagPerfResults[btagWP]['StatisticsUp'][ptbin], opt.bTagPerfResults[btagWP]['StatisticsDown'][ptbin] = {}, {}
            opt.bTagPerfResults[btagWP]['StatisticsUp'][ptbin]['scaleFactor'] = finalScaleFactor + finalScaleFactorUncertainty
            opt.bTagPerfResults[btagWP]['StatisticsDown'][ptbin]['scaleFactor'] = finalScaleFactor - finalScaleFactorUncertainty
            opt.bTagPerfResults[btagWP]['FinalSystematics'][ptbin] = {}
            opt.bTagPerfResults[btagWP]['FinalSystematics'][ptbin]['scaleFactor'] = finalScaleFactor
            opt.bTagPerfResults[btagWP]['FinalSystematics'][ptbin]['scaleFactorUncertainty'] = scaleFactorSystematicUncertainty
            opt.bTagPerfResults[btagWP]['FinalUp'][ptbin], opt.bTagPerfResults[btagWP]['FinalDown'][ptbin] = {}, {} 
            opt.bTagPerfResults[btagWP]['FinalUp'][ptbin]['scaleFactor'] = finalScaleFactor + scaleFactorSystematicUncertainty
            opt.bTagPerfResults[btagWP]['FinalDown'][ptbin]['scaleFactor'] = finalScaleFactor - scaleFactorSystematicUncertainty

def getSystematicsForComparison(opt):

    systematicToCompare = [ ]

    for selection in opt.Selections:
        if selection.replace('Up','').replace('Down','') in opt.option:
            if selection not in systematicToCompare:
                systematicToCompare.append(selection)

    return systematicToCompare

def bTagPerfResults(opt, action='plot'):

    opt.bTagPerfResults = {} 
    optAux = copy.deepcopy(opt)

    for tag in opt.tag.split('-'):

        rawTag = tag.split('__')[0]
        if '_mergedSelections' in tag:
            if  '_mergedSelections' not in rawTag: rawTag += '_mergedSelections'
            if '_nuisSelections' in tag and '_nuisSelections' not in rawTag: rawTag += '_nuisSelections'
        if '_mergedJetPtBins' in tag and '_mergedJetPtBins' not in rawTag: rawTag += '_mergedJetPtBins'       
 
        optAux.tag = rawTag
        getBTagPerfResults(optAux)

        if 'plot' in action or 'store' in action: 
            opt.fitOption = ''
            if 'finalplot' in action or 'store' in action: 
                if '_nuisSelections' in tag: opt.fitOption = '_nuisSelections'    
                computeFinalScaleFactors(optAux)
        opt.bTagPerfResults[rawTag] = optAux.bTagPerfResults
 
def printBTagPerformance(opt):

    bTagPerfResults(opt, action='print')

    for btagWP in opt.btagWPs:
        for ptbin in opt.ptBins:
            print('####', btagWP, ptbin)
            for tag in opt.bTagPerfResults:    
                for systematic in opt.Selections:
                    syst = systematic if systematic!='' else 'Central'
                    bTagPerfShort = opt.bTagPerfResults[tag][btagWP][syst]
                    print('    ', tag, syst, bTagPerfShort[ptbin]['efficiencyMC'], bTagPerfShort[ptbin]['efficiencyFit'], bTagPerfShort[ptbin]['scaleFactor'], bTagPerfShort[ptbin]['scaleFactorUncertainty'])
                print('')

def plotBTagPerformance(opt, resultToPlot='performance', action='plot'):

    if 'DepOn' in opt.option:
        opt.Selections = getSystematicsForComparison(opt)
        if len(opt.Selections)<2: return

    bTagPerfResults(opt, action)   

    if action=='finalplot':
        opt.Selections = [ 'FinalSystematics', 'Final', 'Central' ] if 'central' in opt.option.lower() else [ 'FinalSystematics', 'Final' ]
        opt.option = 'FinalCompared' if len(opt.Selections)>2 else 'Final' 
    elif opt.Selections[0]=='': opt.Selections[0] = 'Central'

    for btagWP in opt.btagWPs:

        bTagPerfHistos = {}

        for tag in opt.bTagPerfResults:
            bTagPerfHistos[tag] = {}
            for systematic in opt.Selections:
                bTagPerfHistos[tag][systematic] = {}
                for result in [ 'efficiencyMC', 'efficiencyFit', 'scaleFactor' ]:
                    if resultToPlot in result.lower() or resultToPlot=='performance':
                        bTagPerfHistos[tag][systematic][result] = fillBTagPerfHistogram(opt, result, btagWP, opt.bTagPerfResults[tag][btagWP][systematic])

        makeBTagPerformancePlot(opt, btagWP, bTagPerfHistos, resultToPlot)

def plotBTagEfficiencies(opt):
 
    plotBTagPerformance(opt, resultToPlot='efficiency')

def plotBTagScaleFactors(opt):

    plotBTagPerformance(opt, resultToPlot='scalefactor') 

def analyzeBTagScaleFactorSytematics(opt):

    resultToPlot = 'performance' if 'performance' in opt.option else 'efficiency' if 'efficiency' in opt.option else 'scalefactor'

    opt.origSelections = opt.Selections

    for systematic in opt.origSelections: 
        if systematic!='' and 'Down' not in systematic:
            opt.option = 'DepOn' + systematic.replace('Up','')
            plotBTagPerformance(opt, resultToPlot)
            opt.Selections = opt.origSelections

def plotFinalBTagScaleFactors(opt):

    plotBTagPerformance(opt, action='finalplot', resultToPlot='scalefactor')

### Store scale factores

def storeBTagScaleFactors(opt):

    ROOT.gROOT.ProcessLine('.L BTagCalibrationStandalone.cpp+')

    operatingPoints = { 'L'   : ROOT.BTagEntry.OperatingPoint.OP_LOOSE, 
                        'M'   : ROOT.BTagEntry.OperatingPoint.OP_MEDIUM, 
                        'T'   : ROOT.BTagEntry.OperatingPoint.OP_TIGHT,
                        'XT'  : ROOT.BTagEntry.OperatingPoint.OP_EXTRATIGHT,
                        'XXT' : ROOT.BTagEntry.OperatingPoint.OP_EXTRAEXTRATIGHT
                       } 

    bTagPerfResults(opt, action='store')

    systematics = [ 'Central' ]
    for systematic in opt.Selections:
        if systematic!='' and 'Down' not in systematic: systematics.append(systematic.replace('Up',''))

    for tag in opt.bTagPerfResults:
 
        if 'publish' in opt.option.lower():
            csvDirectory = '../../../btv-scale-factors/'+opt.csvCampaign+'/csv/btagging_fixedWP_SFb/' 
        else:
            csvDirectory = '/'.join([ '.', 'CSVFiles', tag, opt.year, '' ])
        os.system('mkdir -p '+csvDirectory)

        btagAlgorithms = {}
        for btagAlgorithm in opt.bTagAlgorithms:
            for btagWP in opt.bTagPerfResults[tag]:
                if btagAlgorithm in btagWP:
                    if btagAlgorithm not in btagAlgorithms: btagAlgorithms[btagAlgorithm] = [ btagWP ]
                    else: btagAlgorithms[btagAlgorithm].append(btagWP)
 
        for btagAlgorithm in btagAlgorithms:
             
            csvFileName = btagAlgorithm if len(btagAlgorithms[btagAlgorithm])>1 else btagAlgorithms[btagAlgorithm][0]
            csvFileName = csvFileName.replace(btagAlgorithm, opt.csvBTagAlgorithms[btagAlgorithm])+'_' +opt.csvMethod
            if 'publish' in opt.option.lower(): csvFileName += opt.option.lower().replace('publish_','_').replace('publish','_')
            else: csvFileName += opt.fitOption
            csvFile = ROOT.BTagCalibration(csvFileName+'.csv')

            for btagWP in sorted(btagAlgorithms[btagAlgorithm]):
                for systematic in opt.csvSystematics:
                    if opt.csvSystematics[systematic] in opt.bTagPerfResults[tag][btagWP]:
                        for ptbin in opt.bTagPerfResults[tag][btagWP][opt.csvSystematics[systematic]]:
                            if opt.bTagPerfResults[tag][btagWP][opt.csvSystematics[systematic]][ptbin]['scaleFactor']>0.:

                                ptMin = float(ptbin.replace('Pt','').split('to')[0])
                                ptMax = float(ptbin.replace('Pt','').split('to')[1])
                                params = ROOT.BTagEntry.Parameters(operatingPoints[btagWP.replace(btagAlgorithm,'')], opt.csvMethod, systematic,
                                                                   ROOT.BTagEntry.FLAV_B, 0., opt.maxJetEta, ptMin, ptMax, 0., 1.)

                                entry = ROOT.BTagEntry(str(opt.bTagPerfResults[tag][btagWP][opt.csvSystematics[systematic]][ptbin]['scaleFactor']), params)
                                csvFile.addEntry(entry) 

            with open(csvDirectory+'/'+csvFileName+'.csv', 'w') as f:
                f.write(csvFile.makeNewCSV())
                                
### Working points

def workingPoints(opt): # TODO port to Run3

    if 'WorkingPoints' not in opt.tag: opt.tag = 'WorkingPoints'
    opt.sigset='MCQCD' if 'SM' in opt.sigset or opt.sigset=='MC' else opt.sigset

    wpSamples = []
    for sample in opt.samples:
        if not opt.samples[sample]['isDATA']: wpSamples.append(sample)

    if len(wpSamples)!=1: 
        print('workingPoints error: too many samples selected ->', wpSamples)
        exit()

    inputFile = ROOT.TFile.Open('/'.join([ opt.shapedir, opt.year, opt.tag.split('_')[0], 'Samples', 'plots_'+opt.year+opt.tag.split('_')[0]+'_ALL_'+wpSamples[0]+'.root' ]), 'read')

    bTagAlgorithms = [ 'DeepJet', 'ParticleNet', 'ParT' ]
    workingPointName = [ 'Loose', 'Medium', 'Tight', 'eXtraTight', 'eXtraeXtraTight' ]
    workingPointLimit = [ 0.1, 0.01, 0.001, 0.0005, 0.0001 ]

    for btagAlgo in opt.bTagAlgorithms:
        
        btagDiscriminant = opt.bTagWorkingPoints[btagAlgo+''.join([ x for x in opt.workingPointName[0] if x.isupper() ])]['discriminant']
        bJetDisc = inputFile.Get('QCD/Jet_'+btagDiscriminant+'_5_0/histo_'+wpSamples[0])
        lJetDisc = inputFile.Get('QCD/Jet_'+btagDiscriminant+'_0_0/histo_'+wpSamples[0])

        for ijet in range(1, opt.nJetMax):
            bJetDisc.Add(inputFile.Get('QCD/Jet_'+btagDiscriminant+'_5_'+str(ijet)+'/histo_'+wpSamples[0]))
            lJetDisc.Add(inputFile.Get('QCD/Jet_'+btagDiscriminant+'_0_'+str(ijet)+'/histo_'+wpSamples[0]))

        if 'noprint' not in opt.option:
            print('\n\nWorking Points for', btagAlgo)


        oldWorkingPoint = []
        for wp in opt.workingPointName:
            wpflag = ''.join([ x for x in wp if x.isupper() ])
            if btagAlgo+wpflag in opt.bTagWorkingPoints: oldWorkingPoint.append(float(opt.bTagWorkingPoints[btagAlgo+wpflag]['cut']))
            else: oldWorkingPoint.append(0.9) 

        integralLightJets  = lJetDisc.Integral(0, lJetDisc.GetNbinsX())
        integralBottomJets = bJetDisc.Integral(0, bJetDisc.GetNbinsX())
 
        if 'csv' in opt.option:
            print('   ', btagAlgo, end=' ')
        elif 'yml' in opt.option:
            print(+':')

        for wp in range(len(opt.workingPointName)):

            wpflag = ''.join([ x for x in opt.workingPointName[wp] if x.isupper() ])
            mistagRateDistance =  999.
            binAtWorkingPoint  = -999

            for ib in range(1, bJetDisc.GetNbinsX()+1):

                mistagRate = lJetDisc.Integral(ib, lJetDisc.GetNbinsX())/integralLightJets

                if abs(mistagRate-opt.workingPointLimit[wp])<mistagRateDistance: 

                    mistagRateDistance = abs(mistagRate-opt.workingPointLimit[wp])
                    binAtWorkingPoint = ib

            if 'noprint' not in opt.option:
                print('   ', opt.workingPointName[wp], 'working point:', lJetDisc.GetBinLowEdge(binAtWorkingPoint), '(', lJetDisc.GetBinLowEdge(binAtWorkingPoint-1), ',', lJetDisc.GetBinLowEdge(binAtWorkingPoint+1), ')')
                print('        MistagRate:', lJetDisc.Integral(binAtWorkingPoint, lJetDisc.GetNbinsX())/integralLightJets, '(', lJetDisc.Integral(binAtWorkingPoint-1, lJetDisc.GetNbinsX())/integralLightJets, ', ', lJetDisc.Integral(binAtWorkingPoint+1, lJetDisc.GetNbinsX())/integralLightJets, ') over', integralLightJets)
                print('        Efficiency:', bJetDisc.Integral(binAtWorkingPoint, bJetDisc.GetNbinsX())/integralBottomJets, '(', bJetDisc.Integral(binAtWorkingPoint-1, bJetDisc.GetNbinsX())/integralBottomJets, ', ', bJetDisc.Integral(binAtWorkingPoint+1, bJetDisc.GetNbinsX())/integralBottomJets, ') over', integralBottomJets)

                binOldWorkingPoint = lJetDisc.FindBin(oldWorkingPoint[wp])
                print('        OldWorkingPoint', oldWorkingPoint[wp], lJetDisc.Integral(binOldWorkingPoint, lJetDisc.GetNbinsX())/integralLightJets, bJetDisc.Integral(binOldWorkingPoint, lJetDisc.GetNbinsX())/integralBottomJets, '\n')

            elif 'csv' in opt.option:
                print(lJetDisc.GetBinLowEdge(binAtWorkingPoint), end=' ') 
                print(round((100.*bJetDisc.Integral(binAtWorkingPoint, bJetDisc.GetNbinsX())/integralBottomJets),1), end=' ')
                print(round((100.*lJetDisc.Integral(binAtWorkingPoint, lJetDisc.GetNbinsX())/integralLightJets),1 if opt.workingPointName[wp]=='Loose' else 2), end=' ') 
            elif 'yml' in opt.option:
                print('   ',wpflag+':')
                print('       ', 'eff:', round((100.*bJetDisc.Integral(binAtWorkingPoint, bJetDisc.GetNbinsX())/integralBottomJets),1))
                print('       ', 'wp:', lJetDisc.GetBinLowEdge(binAtWorkingPoint)) 


            if btagAlgo+wpflag not in opt.bTagWorkingPoints:
                opt.bTagWorkingPoints[btagAlgo+wpflag] = {}
                opt.bTagWorkingPoints[btagAlgo+wpflag]['discriminant'] = btagDiscriminant

            opt.bTagWorkingPoints[btagAlgo+wpflag]['cut'] = str(round(lJetDisc.GetBinLowEdge(binAtWorkingPoint),4))

        if 'csv' in opt.option: print('')

    if 'noprint' not in opt.option:
        print('\n\nbTagWorkingPoints =', opt.bTagWorkingPoints, '\n\n') 

### Analysis specific weights, efficiencies, scale factors, etc.

import sys
sys.path.append('/afs/cern.ch/cms/PPD/PdmV/tools/McM/')
from rest import McM

def getGeneratorParametersFromMCM(mcm_query):

    mcm = McM(dev=True)
    requests = mcm.get('requests', None, mcm_query)
    nValidRequests = 0
    for request in requests:
        if request['status']=='done' and ('GEN' in request['prepid'] or 'GS' in request['prepid']):
            xSec = request['generator_parameters'][0]['cross_section']
            fEff = request['generator_parameters'][0]['filter_efficiency']
            nValidRequests += 1

    if nValidRequests==1: return [ xSec, fEff ]
    elif nValidRequests==0: print('No request for', mcm_query, 'query found in McM')
    else: print('Too many requests for', mcm_query, 'query found in McM')
    return [ -1., -1. ]

def ptHatWeights(opt): # TODO port to Run3

    opt.tag = 'PtHatWeights'
    opt.sigset = 'MC'

    for sample in opt.samples:

        ptHatBin = sample.split('_')[-1]
        events = ROOT.TChain(opt.treeName)
        for tree in opt.samples[sample]['name']: events.Add(tree.replace('#',''))
            
        if 'QCDMu_' in sample:
            opt.qcdMuPtHatBins[ptHatBin]['events'] = str(events.GetEntries())
            if not 'xSec' in opt.qcdMuPtHatBins[ptHatBin]: 
                xSec, fEff = getGeneratorParametersFromMCM('dataset_name=QCD_*'+ptHatBin+'_MuEnrichedPt5_*&prepid=BTV*'+opt.year+'G*')
                opt.qcdMuPtHatBins[ptHatBin]['xSec'] = str(xSec)+'*'+str(fEff)
            else:
                genPars = opt.qcdMuPtHatBins[ptHatBin]['xSec'].split('*')
                xSec = float(genPars[0])
                fEff = 1. if len(genPars)==1 else float(genPars[1])
            opt.qcdMuPtHatBins[ptHatBin]['weight'] = str(1000.*xSec*fEff/events.GetEntries())

        elif 'QCD_' in sample:
            opt.qcdPtHatBins[ptHatBin]['events'] = str(events.GetEntries())
            if not 'xSec' in opt.qcdPtHatBins[ptHatBin]:
                xSec, fEff = getGeneratorParametersFromMCM('dataset_name=QCD_*'+ptHatBin+'_Tune*&prepid=BTV*'+opt.year+'G*')
                opt.qcdPtHatBins[ptHatBin]['xSec'] = str(xSec)+'*'+str(fEff)
            else:
                genPars = opt.qcdPtHatBins[ptHatBin]['xSec'].split('*')
                xSec = float(genPars[0])
                fEff = 1. if len(genPars)==1 else float(genPars[1])
            opt.qcdPtHatBins[ptHatBin]['weight'] = str(1000.*xSec*fEff/events.GetEntries())

    print('\nqcdMuPtHatBins =', opt.qcdMuPtHatBins)
    print('\nqcdPtHatBins =', opt.qcdPtHatBins, '\n')

def triggerPrescales(opt): # TODO finish to port to Run3

    campaigns = opt.year.split('-')

    mergeJobs = {}

    for campaign in campaigns:

        commonTools.getConfigParameters(opt, [ 'triggerInfos', 'campaignRunPeriod' ])

        commandList = [ opt.dataConditionScript ]
        commandList.append('--action=ps')
        commandList.append('--years='+opt.campaignRunPeriod['year'])
        commandList.append('--periods='+opt.campaignRunPeriod['period'])
        commandList.append('--outputDir='+commonTools.mergeDirPaths(opt.baseDir,opt.datadir+'/'+campaign))

        for trigger in opt.triggerInfos:
            for hltpath in [ trigger, opt.triggerInfos[trigger]['jetTrigger'] ]:
                if 'hltpath:' in opt.option and hltpath not in opt.option: continue
                if 'hltpathveto:' in opt.option and hltpath in opt.option: continue
                if opt.interactive:
                    os.system(' '.join(commandList)+' --hltPaths=HLT_'+hltpath)
                else:
                    mergeJobs[campaign+'_'+hltpath] = commonTools.cdWorkDir(opt)+' '.join(commandList)+' --hltPaths=HLT_'+hltpath

    if len(list(mergeJobs.keys()))>0:
            latinoTools.submitJobs(opt, 'prescales', campaign+'Prescales', mergeJobs, 'Targets', True, 1)

def triggerPrescalesJSON(opt):

    import csv
    import json

    commonTools.getConfigParameters(opt, [ 'triggerInfos', 'campaignRunPeriod' ])

    triggerPrescalesFilesDir = '/'.join([ opt.datadir, opt.campaign, 'Prescales', '' ])

    bTagMuTriggerPrescales, jetHTTriggerPrescales = {}, {}

    for trigger in opt.triggerInfos:
        for hltPath in [ trigger, opt.triggerInfos[trigger]["jetTrigger"]]:

            triggerPrescales = {}

            triggerPrescalesFileName = triggerPrescalesFilesDir + '_'.join([ 'Prescales', opt.campaignRunPeriod['period'], 'HLT', hltPath ])
            with open(triggerPrescalesFileName+'.csv') as csvfile:
                spamreader = csv.reader(csvfile, delimiter=',')
                for row in spamreader:
                    if '#' not in row[0]:
                        if row[0] not in triggerPrescales: triggerPrescales[row[0]] = {}
                        triggerPrescales[row[0]][row[1]] = row[3]

            if 'BTagMu' in hltPath: bTagMuTriggerPrescales[hltPath] = triggerPrescales
            else: jetHTTriggerPrescales[hltPath] = triggerPrescales
            
            with open(triggerPrescalesFileName+'.json', 'w') as outfile:
                json.dump(triggerPrescales, outfile)

    with open(triggerPrescalesFilesDir + '_'.join([ 'Prescales', opt.campaignRunPeriod['period'], 'HLT_BTagMu' ])+'.json', 'w') as outfile:
        json.dump(bTagMuTriggerPrescales, outfile)

    with open(triggerPrescalesFilesDir + '_'.join([ 'Prescales', opt.campaignRunPeriod['period'], 'HLT_JetHT' ])+'.json', 'w') as outfile:
        json.dump(jetHTTriggerPrescales, outfile)

def kinematicWeights(opt):

    if 'jetpteta' in opt.option.lower():
        print('kinematicWeights in 2D not supported yet')
        exit()

    if 'jetpt' not in opt.option.lower() and 'jeteta' not in opt.option.lower():
        print('kinematicWeights only supported for jetpt and jeteta')
        exit()

    jetPtEdges = []
    for jetBin in opt.jetPtBins:
        for ptEdge in [ float(opt.jetPtBins[jetBin][0]), float(opt.jetPtBins[jetBin][1]) ]:
            if ptEdge not in jetPtEdges:
                jetPtEdges.append(ptEdge)
    jetPtEdges.sort()

    outputDir = '/'.join([ opt.datadir, opt.year, 'Kinematics' ])
    os.system('mkdir -p '+outputDir)

    if 'Light' in opt.tag and 'MergedLight' not in opt.tag:
        mergeLightShapes(opt)
        opt.tag = opt.tag.replace('Light', 'MergedLight')

    samples, cuts, variables = commonTools.getDictionariesInLoop(opt, opt.year, opt.tag, opt.sigset, 'variables')

    data, backgrounds = 'DATA', [ ]
    for sample in samples:
        if sample!='DATA': backgrounds.append(sample)

    data_File = commonTools.openSampleShapeFile(opt.shapedir, opt.year, opt.tag.replace('MergedLight','').split('.')[0], data) 

    kinematicVariable = ''
    for variable in variables: 
        if variable.split('_')[0] in opt.option.lower(): kinematicVariable = variable.split('_')[0]

    if kinematicVariable=='': 
        print('kinematicWeights: no valid variable found for', opt.option.lower())
        exit()

    if 'jetpt' in kinematicVariable:
        xBins = ( int(opt.maxJetPt-opt.minJetPt), opt.minJetPt, opt.maxJetPt )
        yBins = ( 1, -opt.maxJetEta, opt.maxJetEta )
    elif 'jeteta' in kinematicVariable:
        xBins = [ jetPtEdges ]
        yBins = ( int((2.*opt.maxJetEta)/0.1), -opt.maxJetEta, opt.maxJetEta )
    else:
        print('Error in kinematicWeights: no function variable chosen for corrections')
        exit()

    for back in backgrounds:

        inputFile = commonTools.openSampleShapeFile(opt.shapedir, opt.year, opt.tag, back)

        tagkinweights = '' if '.' not in opt.tag else '.'+opt.tag.split('.',1)[-1]
        outputname = opt.method + '_' + back + tagkinweights + '.' + kinematicVariable
        outputFile = commonTools.openRootFile(outputDir+'/'+outputname+'.root', 'recreate')

        weightsHisto = commonTools.bookHistogram(kinematicVariable, xBins, yBins)   

        for cut in cuts:
            for variable in variables:
                if variable.split('_')[0]!=kinematicVariable: continue
                if 'cuts' not in variables[variable] or cut in variables[variable]['cuts']:

                    dataHisto = data_File.Get('/'.join([ cut, variable.replace('lightjet','mujet').replace('jeteta_'+cut,'jeteta'), 'histo_'+data ])) ; dataHisto.SetDirectory(0)
                    backHisto = inputFile.Get('/'.join([ cut, variable                                                            , 'histo_'+back ])) ; backHisto.SetDirectory(0)

                    if 'skipfixspikes' not in opt.option:

                        spikeList = [ ]
                        for ib in range(1, backHisto.GetNbinsX()+1):
                            isSpike = True
                            for shift in [ ib-1, ib+1 ]:
                                if backHisto.GetBinContent(shift)>0.:
                                    if backHisto.GetBinContent(ib)/backHisto.GetBinContent(shift)<1.1:
                                        isSpike = False
                            if isSpike: spikeList.append(ib)

                        for spike in spikeList:
                            spikeContent, spikeShifts = 0., 0
                            for shift in [ spike-1, spike+1 ]:
                                if backHisto.GetBinContent(shift)>0.:
                                    spikeContent += backHisto.GetBinContent(shift)
                                    spikeShifts += 1
                            if spikeShifts>0:
                                spikeContent /= spikeShifts
                                backHisto.SetBinContent(spike, spikeContent)

                    if 'jetpt' in opt.option.lower() or 'jeteta' in opt.option.lower():

                        dataHisto.Divide(backHisto) 

                        if 'jetpt' in opt.option.lower():
                        
                            minPtFit, maxPtFit = dataHisto.GetBinLowEdge(1), dataHisto.GetBinLowEdge(dataHisto.GetNbinsX()+1)
                            ptfit = ROOT.TF1('ptfit', 'pol3', minPtFit, maxPtFit)
                            dataHisto.Fit('ptfit')

                        ptval  = float(opt.jetPtBins[cut][0]) + 0.1
                        etaval = weightsHisto.GetYaxis().GetBinCenter(1)

                        for ib in range(dataHisto.GetNbinsX()):

                            if 'jetpt' in opt.option.lower():
                                ptval  = dataHisto.GetBinCenter(ib+1)
                                weight = ptfit.Eval(dataHisto.GetBinCenter(ib+1))

                            elif 'jeteta' in opt.option.lower():
                                etaval = dataHisto.GetBinCenter(ib+1)
                                weight = dataHisto.GetBinContent(ib+1)

                            weightsHisto.SetBinContent(weightsHisto.FindBin(ptval, etaval), weight)

                            if opt.verbose:
                                print(back, cut, ptval, etaval, weight)

        inputFile.Close()

        outputFile.cd()
        weightsHisto.Write()                        
        outputFile.Close()

    data_File.Close()

