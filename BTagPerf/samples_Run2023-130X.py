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

campaign = year

method = 'System8' if 'System8' in tag else 'PtRel'
bIsSignal = method=='PtRel' and not isPlot

if isFillShape and 'MergedLight' in tag:
    print('Cannot fill shapes for', tag, 'directly from trees')
    exit()

if isShape:
    if 'WorkingPoints' in tag or 'PtHatWeights' in tag or ('.' in tag and 'Light' not in tag): 
        if sigset=='SM': sigset = 'MC'
        elif sigset=='Data': exit()

### Sample directories

SITE=os.uname()[1]
if 'cern' not in SITE and 'ifca' not in SITE and 'cloud' not in SITE: SITE = 'cern'

if 'cern' in SITE:
    treeBaseDirMC   = '/eos/cms/store/group/phys_btag/milee/BTA_addPFMuons'
    treeBaseDirData = '/eos/cms/store/group/phys_btag/milee/BTA_addPFMuons'
else: print('trees for', campaign, 'campaign available only at cern')

ProductionMC   = campaign
ProductionData = campaign
  
directoryBkg  = '/'.join([ treeBaseDirMC,   ProductionMC  , '' ])
directoryData = '/'.join([ treeBaseDirData, ProductionData, '' ])

### Campaign parameters

CME = '13.6'
lumi = 1. if 'Validation' in tag else 9.451 if 'Summer23BPix' in campaign else 17.650

# Pileup scenarios: https://github.com/cms-sw/cmssw/blob/master/SimGeneral/MixingModule/python/
simulationPileupFile = 'pileup_DistrWinter22_Run3_2022_LHC_Simulation_10h_2h.root'
if 'Summer23BPix' in campaign:
    dataPileupFile = '/afs/cern.ch/work/s/scodella/BTagging/CMSSW_13_3_1/src/LatinoAnalysis/NanoGardener/python/data/PUweights/2023/2023D.root'
    simulationPileupList = [ 0.000158878446531, 3.72079495004e-05, 4.81640545476e-05, 4.57853820338e-05, 4.48623875183e-05, 5.84446325801e-05, 6.21371953105e-05, 7.03017263882e-05, 8.14053877829e-05, 8.70272731863e-05, 8.31197017269e-05, 9.10479801679e-05, 0.000157953009035, 0.000116574062554, 0.000129294975462, 0.000144545642223, 0.000217078041821, 0.000440232973883, 0.000773662434135, 0.00110283621902, 0.00142257438371, 0.00176809978781, 0.00208600425923, 0.00241950256675, 0.00296346767304, 0.00376702592516, 0.00484406195225, 0.00613147621346, 0.00769025671271, 0.00948861093862, 0.0109925387243, 0.0123667087551, 0.013627393454, 0.0146345506473, 0.015512752756, 0.0165376249303, 0.0175929813666, 0.018477824153, 0.0192112990472, 0.0196645289817, 0.0201161023712, 0.0206504959528, 0.020879696658, 0.0210625541872, 0.0212334411744, 0.0213619175725, 0.0217040066936, 0.022158015445, 0.0228131566405, 0.0238090615222, 0.0245709343881, 0.0255676600477, 0.0269068441176, 0.0282418222377, 0.0301095236733, 0.0322607862482, 0.0340215193181, 0.0351963407371, 0.0355890314646, 0.0353316943073, 0.0341387294252, 0.0328144650238, 0.0308479015762, 0.0279916459339, 0.0248514911256, 0.0219924532015, 0.0191273076414, 0.0162191660774, 0.0134212379857, 0.0108569317827, 0.00894075906105, 0.00721689444201, 0.00577376618889, 0.0045988410223, 0.00345625399226, 0.00268987667653, 0.00203585450746, 0.00148498442583, 0.00104550889127, 0.000680880800731, 0.000378259194695, 0.000208622992464, 0.000137403591797, 9.84678907631e-05, 6.66619364389e-05, 4.98540448905e-05, 3.6916797972e-05, 2.83299393313e-05, 2.35951729274e-05, 1.47733031993e-05, 1.30753995144e-05, 1.17148517026e-05, 7.73674081622e-06, 4.60860216753e-06, 3.2973125953e-07, 1.89267830307e-07, 6.32999965354e-08, 0.0, 0.0, 0.0 ]
    simulationPileupFile = 'mix_2023_25ns_EraD_PoissonOOTPU_cfi.root'

elif 'Summer23' in campaign:
    dataPileupFile = '/afs/cern.ch/work/s/scodella/BTagging/CMSSW_13_3_1/src/LatinoAnalysis/NanoGardener/python/data/PUweights/2023/2023C.root'
    simulationPileupList = [ 2.38822148706e-05, 4.75152134008e-05, 6.30191527793e-05, 6.68452240771e-05, 8.1025250051e-05, 9.79468565963e-05, 9.95081424719e-05, 9.33708830231e-05, 9.50909917671e-05, 0.000100651134241, 0.000103078257098, 0.000111034560318, 0.000122287617571, 0.000133124512985, 0.00014956573019, 0.000186137627395, 0.000228156756843, 0.000282331058406, 0.000331622711531, 0.000391461449341, 0.000517949289644, 0.000772840072265, 0.00117177950147, 0.00170218286606, 0.00236820136292, 0.00313598312592, 0.00408745219886, 0.00527840094237, 0.00673298586987, 0.00828009786211, 0.00981421228066, 0.0113605372864, 0.0128822615559, 0.0143533259986, 0.0156697830309, 0.0169254217283, 0.018080221643, 0.0189942713703, 0.0198224792894, 0.0205857576279, 0.0212350460744, 0.0217526935632, 0.022272803428, 0.0228031352959, 0.0231877786772, 0.0236794597607, 0.0242098757217, 0.0250255926642, 0.0259084771241, 0.0270883359038, 0.0283842141201, 0.0296138041433, 0.0312398518545, 0.0328769694128, 0.0343573284679, 0.0359444082242, 0.0371707283039, 0.0379191373689, 0.0376984798185, 0.0364701631509, 0.0342333461199, 0.030918081708, 0.02719246186, 0.0234422219723, 0.0199428306976, 0.0167530883095, 0.0139446903019, 0.0115684641268, 0.0095875821463, 0.00792109671955, 0.00642645801884, 0.00514147006535, 0.004014647174, 0.00312068891816, 0.00254047982771, 0.00206998047115, 0.00170256713492, 0.00142457093791, 0.00112986818813, 0.000874387606181, 0.000666515127689, 0.000479354340271, 0.000316491543232, 0.000182306321277, 9.7983507813e-05, 5.59397929391e-05, 3.25116880719e-05, 2.05226891643e-05, 1.08317242834e-05, 4.61503191047e-06, 1.49869506368e-06, 3.4791503138e-07, 1.59930964479e-08, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0 ]
    simulationPileupFile = 'mix_2023_25ns_EraC_PoissonOOTPU_cfi.root'

# b fragmentation
bFragDataDir = '/'.join([ os.path.abspath('Data'), 'BFragmentationWeights', '' ])
bfragweightFile = bFragDataDir + 'bfragweights_vs_pt.root'
bdecayweightsFile = bFragDataDir + 'bdecayweights.root'
fragTune = 'fragCP5BL'

# JEU
jetEnergyUncertaintyFile = 'Summer23BPixPrompt23_V1_MC_Uncertainty_AK4PFPuppi.txt' if 'Summer23BPix' in campaign else 'Summer23Prompt23_V1_MC_Uncertainty_AK4PFPuppi.txt'

# global parameters
minJetPt  =   20.
maxJetPt  = 1400.
maxJetEta = '2.5'
minPlotPt =   20.
maxPlotPt = 1000.

campaignRunPeriod = { 'year' : '2023' }
campaignRunPeriod['period']    = '2023D' if 'Summer23BPix' in campaign else '2023C'
campaignRunPeriod['pileup']    = campaign
campaignRunPeriod['prescales'] = campaign

ptRelRange = (50, 0., 4.) if method=='PtRel' else (70, 0., 7.)

# triggers
triggerInfos = { 'BTagMu_AK4DiJet20_Mu5'  : { 'jetPtRange' : [  '20.',   '50.' ], 'ptAwayJet' : 20., 'ptTriggerEmulation' :  30., 'jetTrigger' :  'PFJet40', 'idx' : 32, 'idxJetTrigger' : 0 },
                 'BTagMu_AK4DiJet40_Mu5'  : { 'jetPtRange' : [  '50.',  '100.' ], 'ptAwayJet' : 30., 'ptTriggerEmulation' :  50., 'jetTrigger' :  'PFJet40', 'idx' : 33, 'idxJetTrigger' : 0 },
                 'BTagMu_AK4DiJet70_Mu5'  : { 'jetPtRange' : [ '100.',  '140.' ], 'ptAwayJet' : 30., 'ptTriggerEmulation' :  80., 'jetTrigger' :  'PFJet60', 'idx' : 34, 'idxJetTrigger' : 1 },
                 'BTagMu_AK4DiJet110_Mu5' : { 'jetPtRange' : [ '140.',  '200.' ], 'ptAwayJet' : 30., 'ptTriggerEmulation' : 140., 'jetTrigger' :  'PFJet80', 'idx' : 35, 'idxJetTrigger' : 2 },
                 'BTagMu_AK4DiJet170_Mu5' : { 'jetPtRange' : [ '200.',  '320.' ], 'ptAwayJet' : 30., 'ptTriggerEmulation' : 200., 'jetTrigger' : 'PFJet140', 'idx' : 36, 'idxJetTrigger' : 3 },
                 'BTagMu_AK4Jet300_Mu5'   : { 'jetPtRange' : [ '320.', '1400.' ], 'ptAwayJet' : 30., 'ptTriggerEmulation' :   0., 'jetTrigger' : 'PFJet260', 'idx' : 37, 'idxJetTrigger' : 5 },
                }

applyTriggerEmulation = 'true' if method=='PtRel' else 'false'

# b-tagging algorithms and working points
bTagAlgorithms = { 'DeepJet' : 'DeepFlavourBDisc', 'ParticleNet' : 'PNetBDisc' , 'ParT' : 'ParTBDisc' }
workingPointName = [ 'Loose', 'Medium', 'Tight', 'eXtraTight', 'eXtraeXtraTight' ]
workingPointLimit = [ 0.1, 0.01, 0.001, 0.0005, 0.0001 ]

if campaign=='Summer23BPix':
    bTagWorkingPoints = {'DeepJetT' : '0.6563', 'ParticleNetXT' : '0.7544', 'ParTL' : '0.0683', 'ParticleNetM' : '0.1919', 'ParticleNetL' : '0.0359', 'ParTM' : '0.3494', 'ParTT' : '0.7994', 'ParticleNetT' : '0.6133', 'DeepJetM' : '0.2435', 'DeepJetL' : '0.048', 'ParticleNetXXT' : '0.9688', 'ParTXXT' : '0.9883', 'ParTXT' : '0.8877', 'DeepJetXXT' : '0.9483', 'DeepJetXT' : '0.7671'}
    btagAwayJetTagger, btagAwayJetDiscriminant = 'JBP', 'Bprob'
    btagAwayJetVariations = { 'AwayJetTag' : '2.551',  'AwayJetDown' : '1.215' , 'AwayJetUp' : '5.173' }

elif campaign=='Summer23':
    bTagWorkingPoints = {'DeepJetT' : '0.6553', 'ParticleNetXT' : '0.7515', 'ParTL' : '0.0681', 'ParticleNetM' : '0.1917', 'ParticleNetL' : '0.0358', 'ParTM' : '0.3487', 'ParTT' : '0.7969', 'ParticleNetT' : '0.6172', 'DeepJetM' : '0.2431', 'DeepJetL' : '0.0479', 'ParticleNetXXT' : '0.9659', 'ParTXXT' : '0.9883', 'ParTXT' : '0.8882', 'DeepJetXXT' : '0.9459', 'DeepJetXT' : '0.7667'}
    btagAwayJetTagger, btagAwayJetDiscriminant = 'JBP', 'Bprob'
    btagAwayJetVariations = { 'AwayJetTag' : '2.555',  'AwayJetDown' : '1.221' , 'AwayJetUp' : '5.134' }

if 'WorkingPoints' in tag or ('PtRelTemplates' in tag and 'ForFit' not in tag):
    bTagAlgorithms['JBP'] = 'Bprob'
    bTagWorkingPoints[btagAwayJetTagger+'T'] = btagAwayJetVariations['AwayJetUp']
    if 'WorkingPoints' in tag:
        bTagWorkingPoints[btagAwayJetTagger+'L'] = btagAwayJetVariations['AwayJetDown']
        bTagWorkingPoints[btagAwayJetTagger+'M'] = btagAwayJetVariations['AwayJetTag']

if 'btag' in tag:
    btagWPToRemove = []
    for btagwp in bTagWorkingPoints:
        if 'btagveto' in tag:
           if tag.split('btagveto')[1].split('_')[0] in btagwp:
               btagWPToRemove.append(btagwp)
        elif tag.split('btag')[1].split('_')[0] not in btagwp:
           btagWPToRemove.append(btagwp)
    for btagwp in btagWPToRemove:
        del bTagWorkingPoints[btagwp]

# jet pt bins
if 'ProdFine' in tag or 'Validation' in tag:
    jetPtBins = { 'Pt20to30'    : [   '20.',   '30.' ], 'Pt30to40'     : [   '30.',   '40.' ], 'Pt40to50'    : [   '40.',   '50.' ], 'Pt50to60'     : [   '50.',   '60.' ], 
                  'Pt60to70'    : [   '60.',   '70.' ], 'Pt70to80'     : [   '70.',   '80.' ], 'Pt80to100'   : [   '80.',  '100.' ], 'Pt100to120'   : [  '100.',  '120.' ], 
                  'Pt120to140'  : [  '120.',  '140.' ], 'Pt140to160'   : [  '140.',  '160.' ], 'Pt160to200'  : [  '160.',  '200.' ], 'Pt200to260'   : [  '200.',  '260.' ], 
                  'Pt260to300'  : [  '260.',  '300.' ], 'Pt300to320'   : [  '300.',  '320.' ], 'Pt320to400'  : [  '320.',  '400.' ], 'Pt400to500'   : [  '400.',  '500.' ], 
                  'Pt500to600'  : [  '500.',  '600.' ], 'Pt600to800'   : [  '600.',  '800.' ], 'Pt800to1000' : [  '800.', '1000.' ], 'Pt1000to1400' : [ '1000.', '1400.' ], 
                 }
elif 'ProdRun2' in tag or ('Templates' in tag and 'Prod' not in tag):
    jetPtBins = { 'Pt20to30'    : [   '20.',   '30.' ], 'Pt30to50'     : [   '30.',   '50.' ], 'Pt50to70'    : [   '50.',   '70.' ], 'Pt70to100'    : [   '70.',  '100.' ], 
                  'Pt100to140'  : [  '100.',  '140.' ], 'Pt140to200'   : [  '140.',  '200.' ], 'Pt200to300'  : [  '200.',  '300.' ], 'Pt300to600'   : [  '300.',  '600.' ], 
                  'Pt600to1000' : [  '600.', '1000.' ], 'Pt1000to1400' : [ '1000.', '1400.' ], 
                 }
else: 
    jetPtBins = { }
    for trigger in triggerInfos:
        jetPtBins[trigger] = triggerInfos[trigger]['jetPtRange']

if 'JetPt' in tag:
    ptBinToRemove = []
    for ptbin in jetPtBins:
        if 'JetPtVeto' in tag:
           if ptbin in 'Pt'+tag.split('JetPtVeto')[1].split('_')[0]:
               ptBinToRemove.append(ptbin)
        elif ptbin not in 'Pt'+tag.split('JetPt')[1].split('_')[0]:
           ptBinToRemove.append(ptbin)
    for ptbin in ptBinToRemove:
        del jetPtBins[ptbin]

### Systematics

csvSystematics = OrderedDict()
csvSystematics['central'] = 'Final'
for variation in [ 'Up', 'Down' ]:
    csvSystematics[variation.lower()]                   = 'Final'+variation
    csvSystematics[variation.lower()+'_statistic']      = 'Statistics'+variation
    csvSystematics[variation.lower()+'_jetaway']        = 'AwayJet'+variation
    csvSystematics[variation.lower()+'_mupt']           = 'MuPt'+variation
    csvSystematics[variation.lower()+'_mudr']           = 'MuDR'+variation
    csvSystematics[variation.lower()+'_jes']            = 'JEU'+variation
    csvSystematics[variation.lower()+'_pileup']         = 'pileup'+variation
    csvSystematics[variation.lower()+'_gluonsplitting'] = 'gluonSplitting'+variation
    csvSystematics[variation.lower()+'_bfragmentation'] = 'bfragmentation'+variation
    csvSystematics[variation.lower()+'_bdecays']        = 'bdecays'+variation
    csvSystematics[variation.lower()+'_btempcorr']      = 'CorrB'+variation
    csvSystematics[variation.lower()+'_cjets']          = 'cjets'+variation
    csvSystematics[variation.lower()+'_l2c']            = 'lightCharmRatio'+variation
    csvSystematics[variation.lower()+'_ltempcorr']      = 'CorrL'+variation

systematicVariations = [ '' ]

if 'Templates' in tag:

    systematicVariations.extend([ 'MuPtUp', 'MuPtDown', 'MuDRUp', 'MuDRDown' ])
    if 'Light' not in tag:
        systematicVariations.insert(1, 'AwayJetDown')
        systematicVariations.insert(1, 'AwayJetUp')

    systematicNuisances = []

    applyBFragmentation = 1

    if 'NoPU' not in tag and 'Validation' not in tag: systematicNuisances.append('pileup')
    systematicNuisances.append('jeu')
    systematicNuisances.append('gluonSplitting')
    if applyBFragmentation>=1: systematicNuisances.append('bfragmentation')
    systematicNuisances.append('bdecay')
    if method=='PtRel': systematicNuisances.append('lightCharmRatio')

    if 'ForFit' in tag and '_nuisSelections' in tag: 
        for nuisance in systematicNuisances:
            systematicVariations.append(nuisance+'Up')
            systematicVariations.append(nuisance+'Down')

    # Template corrections

    templateTreatments = [ 'corr', 'nuis', 'syst' ]
    bTemplateCorrector = {}
    for btagWP in bTagWorkingPoints: bTemplateCorrector[btagWP] = 'ParTT' if 'DeepJet' in btagWP else 'DeepJetT'

    if 'PtRelTemplates' in tag and 'ForFit' in tag:
    
       templateTreatmentFlag = tag.split('Templates')[1].split('2D')[0].split('ForFit')[0]

       templateCorrectionNuisances = {}   
       if 'Nuis' in templateTreatmentFlag:
           for flavour in templateTreatmentFlag.split('Nuis')[1].split('Syst')[0]:
               templateCorrectionNuisances['Corr'+flavour] = flavour.lower()+'jets'

       if 'Syst' in templateTreatmentFlag and 'nocorrrefit' not in tag and 'norefit' not in tag:
           for flavour in templateTreatmentFlag.split('Syst')[1]:
               systematicVariations.append('Corr'+flavour) 

    if '_sel' in tag:
        selectionToRemove = []
        for tagon in tag.split('_'):
            if 'sel' in tagon:
                for selection in systematicVariations:
                    sel = 'Central' if selection=='' else selection
                    if 'veto' in tagon:
                        if sel in tagon: selectionToRemove.append(selection)
                    elif sel not in tagon: selectionToRemove.append(selection)
                for nuisance in systematicNuisances:
                    for variation in [ 'Up', 'Down' ]:
                        if nuisance+variation in tagon: systematicVariations.append(nuisance+variation)
        for selection in selectionToRemove:
            systematicVariations.remove(selection)

### Selection variables

# muon kinematics selection
  
if 'PtRel' in method:
    softMuonSelectionArgs = '3, {'+str(minJetPt)+', 30., 80.}'
    if   'MuPtUp'   in tag: softMuonSelectionArgs += ', {8., 8., 8.}'
    elif 'MuPtDown' in tag: softMuonSelectionArgs += ', {6., 6., 6.}'
    else:                   softMuonSelectionArgs += ', {5., 5., 5.}'
    if   'MuDRUp'   in tag: softMuonSelectionArgs += ', {999., 999., 999.}'
    elif 'MuDRDown' in tag: softMuonSelectionArgs += ', {0.15, 0.12, 0.09}'
    else:                   softMuonSelectionArgs += ', {0.20, 0.15, 0.12}'

elif 'System8' in method:
    softMuonSelectionArgs = '1, {'+str(minJetPt)+'}'
    if   'MuPtUp'   in tag: softMuonSelectionArgs += ', {8.}'
    elif 'MuPtDown' in tag: softMuonSelectionArgs += ', {6.}'
    else:                   softMuonSelectionArgs += ', {5.}'
    if   'MuDRUp'   in tag: softMuonSelectionArgs += ', {999.}'
    elif 'MuDRDown' in tag: softMuonSelectionArgs += ', {0.30}'
    else:                   softMuonSelectionArgs += ', {0.40}'

# pt-hat safety thresholds

if 'Light' not in tag:
    pthatThresholds = {   '15to20' :  '60.',   '20to30' :  '85.',   '30to50' : '120.',   '50to80' : '160.',  '80to120' : '220.', 
                        '120to170' : '320.', '170to300' : '440.', '300to470' : '620.', '470to600' : '720.', '600to800' : '920.' }
else:
    #pthatThresholds = {  30. : 200.,  50. : 200.,  80. : 200., 120. : 250., 170. : 340., 300. : 520. }
    pthatThresholds = {  80. : 200., 120. : 250., 170. : 340., 300. : 520. }

# Jet pt
jetPt   = 'Jet_pT'
if 'RawPt'   in tag: jetPt = 'Jet_uncorrpt'

# muon-jet selection
mustBeUnique = 'true'

# away jet selection
awayJetTagSelection = 'AwayJetTag'
for systvar in systematicVariations:
    if 'AwayJet' in systvar and systvar in tag: awayJetTagSelection = systvar

if 'PtRel' in method:
    awayJetSelectionArgs     = ','.join([ 'true', 'false', str(minJetPt), maxJetEta, '1.5', btagAwayJetVariations[awayJetTagSelection] ])
    #awayJetLightCut = 'Sum$('+jetSel+' && '+awayDeltaR.replace(muJetIdx,'JETIDX')+'>1.5 && '+jetPt+'>=AWAYJETPTCUT)>=1'

elif 'System8' in method:
    awayJetSelectionArgs     = ','.join([ 'false', 'true', str(minJetPt), maxJetEta, '-1.', '-999999.' ])
    awayJetBTagSelectionArgs = ','.join([ 'false', 'true', str(minJetPt), maxJetEta, '-1.', btagAwayJetVariations[awayJetTagSelection] ])

### Complex variables

# event
nJetMax = 20

# light jets
lightJetSel = '((JETIDX<nJet)*(Alt$(Jet_tightID[JETIDX],0)==1)*(abs(Alt$(Jet_eta[JETIDX],5.))<'+maxJetEta+')*(Alt$('+jetPt+'[JETIDX],-1.)>=PTMIN)*(Alt$('+jetPt+'[JETIDX],999999.)<PTMAX)*(Sum$(PFMuon_GoodQuality>=1 && PFMuon_IdxJet==JETIDX)==0)*(Sum$(Jet_tightID==1 && '+jetPt+'!='+jetPt+'[JETIDX] && Jet_'+btagAwayJetDiscriminant+'>='+btagAwayJetVariations['AwayJetDown']+')==0))'
lightJetPt     = 'Alt$('+jetPt+'[JETIDX],-999.)'
lightJetEta    = 'Alt$(Jet_eta[JETIDX],-999.)'

# light tracks
nLightTrkMax  = 50
trackJetIdx   = 'TrkInc_jetIdx'
trakPt        = 'TrkInc_pt'
#trackJetDR    = muJetDR.replace(muJetIdx,'JETIDX').replace(muPhi,'TrkInc_phi[TRKIDX]').replace(muEta,'TrkInc_eta[TRKIDX]')
lightTrkPtRel = 'Alt$(TrkInc_ptrel[TRKIDX],-999.)'
#lightTrkSel   = '((TRKIDX<nTrkInc)*(Alt$('+trackJetIdx+'[TRKIDX],-1)>=0)*(Alt$('+trakPt+'[TRKIDX],0.)>TRKPTCUT)*(abs(Alt$(TrkInc_eta[TRKIDX],5.))<2.4)*('+trackJetDR+'<TRKDRCUT))'
#nLightTrkJet  = 'Sum$('+trackJetIdx+'==JETIDX && '+trakPt+'>TRKPTCUT && abs(TrkInc_eta)<2.4 && '+trackJetDR.replace('[TRKIDX]','')+'<TRKDRCUT)'

### MC

if 'SM' in sigset or 'MC' in sigset:

    qcdMuName = 'QCD_PT-PTHATBIN_MuEnrichedPt5_TuneCP5_13p6TeV_pythia8'
    qcdName   = 'QCD_PT-PTHATBIN_TuneCP5_13p6TeV_pythia8'
    ttbarName = 'TTto4Q_TuneCP5_13p6TeV_powheg-pythia8'

    if campaign=='Summer23BPix':
        qcdMuPtHatBins = {'80to120': {'ext': '', 'xSec': '2536000*0.03807', 'events': '26692302', 'weight': '3.616979906791104'}, '170to300': {'ext': '', 'xSec': '114200*0.06781', 'events': '33019106', 'weight': '0.2345279124153149'}, '300to470': {'ext': '', 'xSec': '7678*0.09136', 'events': '31598705', 'weight': '0.022199076829256134'}, '600to800': {'ext': '', 'xSec': '180.6*0.1176', 'events': '22802000', 'weight': '0.0009314340847294096'}, '800to1000': {'ext': '', 'xSec': '30.89*0.1278', 'events': '41002587', 'weight': '9.628031519084393e-05'}, '120to170': {'ext': '', 'xSec': '444900*0.05214', 'events': '22380325', 'weight': '1.036494599609255'}, '50to80': {'ext': '', 'xSec': '15710000*0.0221', 'events': '12720414', 'weight': '27.29400159460219'}, '30to50': {'ext': '', 'xSec': '114100000*0.01303', 'events': '31914516', 'weight': '46.58453852159312'}, '470to600': {'ext': '', 'xSec': '630.3*0.1062', 'events': '22833444', 'weight': '0.002931570900999429'}, '15to20': {'ext': '', 'xSec': '907100000*0.0032', 'events': '4999753', 'weight': '580.5726802904063'}, '20to30': {'ext': '', 'xSec': '420500000*0.00599', 'events': '33189564', 'weight': '75.89117470780876'}, '1000': {'ext': '', 'xSec': '9.935*0.1341', 'events': '15340005', 'weight': '8.68502650422865e-05'}}
        qcdPtHatBins = {'80to120': {'ext': '', 'xSec': '2762530*1', 'events': '8967000', 'weight': '308.0773948923832'}, '170to300': {'ext': '', 'xSec': '19204300', 'events': '8688750', 'weight': '2210.2488850525106'}, '300to470': {'ext': '', 'xSec': '7823', 'events': '17354000', 'weight': '0.45078944335599863'}, '600to800': {'ext': '', 'xSec': '186.9', 'events': '20342000', 'weight': '0.009187887130075706'}, '1000to1400': {'ext': '', 'xSec': '9.4183', 'events': '5976000', 'weight': '0.001576020749665328'}, '800to1000': {'ext': '', 'xSec': '32.293', 'events': '11908000', 'weight': '0.0027118743701713133'}, '120to170': {'ext': '', 'xSec': '471100', 'events': '8964000', 'weight': '52.554663096831774'}, '1400to1800': {'ext': '', 'xSec': '0.84265', 'events': '1794000', 'weight': '0.0004697045707915273'}, '1800to2400': {'ext': '', 'xSec': '0.114943', 'events': '900000', 'weight': '0.00012771444444444445'}, '2400to3200': {'ext': '', 'xSec': '0.00682981', 'events': '581000', 'weight': '1.175526678141136e-05'}, '3200': {'ext': '', 'xSec': '0.000165445', 'events': '240000', 'weight': '6.893541666666667e-07'}, '50to80': {'ext': '', 'xSec': '19204300', 'events': '5988000', 'weight': '3207.130928523714'}, '30to50': {'ext': '', 'xSec': '114100000', 'events': '1199270', 'weight': '95141.2109032995'}, '470to600': {'ext': '', 'xSec': '648.2', 'events': '8382000', 'weight': '0.07733237890718206'}, '15to30': {'ext': '', 'xSec': '1327600000', 'events': '1198520', 'weight': '1107699.4960451224'}}
 
    elif campaign=='Summer23':
        qcdMuPtHatBins = {'80to120': {'ext': '', 'xSec': '2536000*0.03807', 'events': '26526706', 'weight': '3.639559318069873'}, '170to300': {'ext': '', 'xSec': '114200*0.06781', 'events': '32267222', 'weight': '0.23999283235476543'}, '300to470': {'ext': '', 'xSec': '7678*0.09136', 'events': '31532825', 'weight': '0.02224545628246121'}, '600to800': {'ext': '', 'xSec': '180.6*0.1176', 'events': '22710862', 'weight': '0.0009351719014452203'}, '800to1000': {'ext': '', 'xSec': '30.89*0.1278', 'events': '40933077', 'weight': '9.64438124209426e-05'}, '120to170': {'ext': '', 'xSec': '444900*0.05214', 'events': '21827015', 'weight': '1.0627695083363438'}, '50to80': {'ext': '', 'xSec': '15710000*0.0221', 'events': '12720414', 'weight': '27.29400159460219'}, '30to50': {'ext': '', 'xSec': '114100000*0.01303', 'events': '31914516', 'weight': '46.58453852159312'}, '470to600': {'ext': '', 'xSec': '630.3*0.1062', 'events': '22598146', 'weight': '0.00296209520904945'}, '15to20': {'ext': '', 'xSec': '907100000*0.0032', 'events': '4999753', 'weight': '580.5726802904063'}, '20to30': {'ext': '', 'xSec': '420500000*0.00599', 'events': '33189564', 'weight': '75.89117470780876'}, '1000': {'ext': '', 'xSec': '9.935*0.1341', 'events': '15219182', 'weight': '8.753975739300575e-05'}}
        qcdPtHatBins = {'80to120': {'ext': '', 'xSec': '2762530*1', 'events': '8967000', 'weight': '308.0773948923832'}, '170to300': {'ext': '', 'xSec': '19204300', 'events': '8602750', 'weight': '2232.344308506001'}, '300to470': {'ext': '', 'xSec': '7823', 'events': '17354000', 'weight': '0.45078944335599863'}, '600to800': {'ext': '', 'xSec': '186.9', 'events': '20084000', 'weight': '0.009305915156343358'}, '1000to1400': {'ext': '', 'xSec': '9.4183', 'events': '5976000', 'weight': '0.001576020749665328'}, '800to1000': {'ext': '', 'xSec': '32.293', 'events': '11908000', 'weight': '0.0027118743701713133'}, '120to170': {'ext': '', 'xSec': '471100', 'events': '8964000', 'weight': '52.554663096831774'}, '1400to1800': {'ext': '', 'xSec': '0.84265', 'events': '1794000', 'weight': '0.0004697045707915273'}, '1800to2400': {'ext': '', 'xSec': '0.114943', 'events': '900000', 'weight': '0.00012771444444444445'}, '2400to3200': {'ext': '', 'xSec': '0.00682981', 'events': '581000', 'weight': '1.175526678141136e-05'}, '3200': {'ext': '', 'xSec': '0.000165445', 'events': '240000', 'weight': '6.893541666666667e-07'}, '50to80': {'ext': '', 'xSec': '19204300', 'events': '5988000', 'weight': '3207.130928523714'}, '30to50': {'ext': '', 'xSec': '114100000', 'events': '1199270', 'weight': '95141.2109032995'}, '470to600': {'ext': '', 'xSec': '648.2', 'events': '8382000', 'weight': '0.07733237890718206'}, '15to30': {'ext': '', 'xSec': '1327600000', 'events': '1198520', 'weight': '1107699.4960451224'}}

    if 'Validation' in tag:
        for pthatbin in list(qcdMuPtHatBins.keys()):
            if pthatbin!='80to120': del qcdMuPtHatBins[pthatbin]
        for pthatbin in list(qcdPtHatBins.keys()):
            if pthatbin!='80to120': del qcdPtHatBins[pthatbin]

    if 'WorkingPoints' in tag or 'PtHatWeights' in tag or 'Light' in tag:

        nPtHatBins = len(list(qcdPtHatBins.keys()))        

        qcdTrees = []
        for pth in qcdPtHatBins:
            if pth=='80to120' or 'WorkingPoints' not in tag:
                ptHatTrees = nanoGetSampleFiles(directoryBkg+qcdName.replace('PTHATBIN',pth)+qcdPtHatBins[pth]['ext']+'/','PT-'+pth, '')
                if 'PtHatWeights' in tag: samples['QCD_'+pth] = { 'name' : ptHatTrees }
                else: qcdTrees += ptHatTrees

        if 'WorkingPoints' in tag or 'Light' in tag:
            samples['QCD'] = { 'name' : qcdTrees, 'weight' : '1.', 'isSignal' : 0 }

        if isFillShape and 'WorkingPoints' not in tag and 'PtHatWeights' not in tag and 'Validation' not in tag:
            for sample in samples:
                for pth in qcdPtHatBins:
                    addSampleWeight(samples, sample, 'PT-'+pth, qcdPtHatBins[pth]['weight'])

    if 'PtHatWeights' in tag or method+'Kinematics' in tag or method+'Templates' in tag:

        nPtHatBins = len(list(qcdMuPtHatBins.keys()))

        qcdMuTrees = []
        for pth in qcdMuPtHatBins:
            ptHatTrees = nanoGetSampleFiles(directoryBkg+qcdMuName.replace('PTHATBIN',pth)+qcdMuPtHatBins[pth]['ext']+'/','PT-'+pth,'')
            if 'PtHatWeights' in tag: samples['QCDMu_'+pth] = { 'name' : ptHatTrees }
            else: qcdMuTrees += ptHatTrees

        if method+'Kinematics' in tag:
            samples['QCDMu'] = { 'name' : qcdMuTrees, 'weight'   : '(1.)'               , 'isSignal' : 1 }

        elif method+'Templates' in tag:
            samples['bjets'] = { 'name' : qcdMuTrees, 'weight'   : 'muonJetFromB', 'isSignal' : bIsSignal }
            if 'PtRel' in method:
                if '2D' not in tag: samples['cjets'] = { 'name' : qcdMuTrees, 'weight'   : 'muonJetFromC', 'isSignal' : 0 }
                samples['ljets'] = { 'name' : qcdMuTrees, 'weight'   : 'muonJetFromL', 'isSignal' : 0 }
            elif 'System8' in method:
                samples['light'] = { 'name' : qcdMuTrees, 'weight'   : 'muonJetNotFromB', 'isSignal' : 0 }

        if isFillShape and 'PtHatWeights' not in tag and 'Validation' not in tag:
            for sample in samples:
                for pth in qcdMuPtHatBins:
                    qcdMuPtHatBinWeight = qcdMuPtHatBins[pth]['weight']
                    if pth in pthatThresholds: qcdMuPtHatBinWeight += '*(muonJetPt<'+pthatThresholds[pth]+')'
                    addSampleWeight(samples, sample, 'PT-'+pth, qcdMuPtHatBinWeight)

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

    dataSetName = 'BTagMu' if 'Light' not in tag else 'JetMET'

    runPeriods = {}
    if 'Summer23BPix' in campaign:
        if dataSetName=='BTagMu':
            runPeriods['Run2023D1'] = { 'subdir' : dataSetName + 'Run2023D-22Sep2023_v1-v1' }
            runPeriods['Run2023D2'] = { 'subdir' : dataSetName + 'Run2023D-22Sep2023_v2-v1' }
        else:  
            runPeriods['Run2023D1'] = { 'subdir' : dataSetName + '0Run2023D-22Sep2023_v1-v1' }
            runPeriods['Run2023D2'] = { 'subdir' : dataSetName + '0Run2023D-22Sep2023_v2-v1' }
            runPeriods['Run2023D3'] = { 'subdir' : dataSetName + '1Run2023D-22Sep2023_v1-v1' }
            runPeriods['Run2023D4'] = { 'subdir' : dataSetName + '1Run2023D-22Sep2023_v2-v1' }
    elif 'Summer23' in campaign:
        if dataSetName=='BTagMu':
            runPeriods['Run2023C1'] = { 'subdir' : dataSetName + 'Run2023C-22Sep2023_v1-v1' }
            runPeriods['Run2023C2'] = { 'subdir' : dataSetName + 'Run2023C-22Sep2023_v2-v1' }
            runPeriods['Run2023C3'] = { 'subdir' : dataSetName + 'Run2023C-22Sep2023_v3-v1' }
            runPeriods['Run2023C4'] = { 'subdir' : dataSetName + 'Run2023C-22Sep2023_v4-v1' }
        else:
            runPeriods['Run2023C1'] = { 'subdir' : dataSetName + '0Run2023C-22Sep2023_v1-v1' }
            runPeriods['Run2023C2'] = { 'subdir' : dataSetName + '0Run2023C-22Sep2023_v2-v1' }
            runPeriods['Run2023C3'] = { 'subdir' : dataSetName + '0Run2023C-22Sep2023_v3-v1' }
            runPeriods['Run2023C4'] = { 'subdir' : dataSetName + '0Run2023C-22Sep2023_v4-v1' }
            runPeriods['Run2023C5'] = { 'subdir' : dataSetName + '1Run2023C-22Sep2023_v1-v1' }
            runPeriods['Run2023C6'] = { 'subdir' : dataSetName + '1Run2023C-22Sep2023_v2-v1' }
            runPeriods['Run2023C7'] = { 'subdir' : dataSetName + '1Run2023C-22Sep2023_v3-v1' }
            runPeriods['Run2023C8'] = { 'subdir' : dataSetName + '1Run2023C-22Sep2023_v4-v1' }

    dataTrees = [ ]
    for runPeriod in runPeriods:
  
        dataDir = '/'.join([ directoryData, runPeriods[runPeriod]['subdir'], '' ]) 
        dataTrees += nanoGetSampleFiles(dataDir, runPeriods[runPeriod]['subdir'], '')
 
    dataName = 'DATA' if dataSetName=='BTagMu' else 'Jet'
    samples[dataName]  = { 'name'      : dataTrees ,
                           'weight'    : '1.' ,
                           'isData'    : ['all'] ,
                           'isSignal'  : 0 ,
                           'isDATA'    : 1 ,
                           'isFastsim' : 0 ,
                           'JobsPerSample' : 40*len(list(runPeriods.keys())) if 'Light' in tag else 8*len(list(runPeriods.keys()))
                          }
     
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

