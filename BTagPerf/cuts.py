from copy import deepcopy

### Methods

def andCuts(cutList, addParentheses=False):
    totalCut = ' && '.join([ x for x in cutList if x!='' ])
    if addParentheses: return '('+totalCut+')'
    else: return totalCut

def orCuts(cutList, operator = ' || '):
    return '(' + operator.join([ '('+x+')' for x in cutList if x!='' ]) + ')'

###

cuts = {}

preselectionList = [ 'goodPV' ]

if 'WorkingPoints' in tag:

    cuts['QCD'] = 'true'

elif 'PtRelTemplates' in tag and 'ForFit' in tag:

    for ptbin in jetPtBins:
        for btagwp in bTagWorkingPoints:
            for btagselection in [ 'Pass', 'Fail' ]:
                for selection in systematicVariations:
                    cuts['_'.join([x for x in [ ptbin, btagwp, btagselection, selection ] if x!=''])] = 'true'

else:

    if 'Light' not in tag: preselectionList.extend([ 'softMuonSelection', 'muonJetSelection', 'triggerSelection', 'awayJetSelection' ])

    for ptbin in jetPtBins:

        if '_Pt' in tag and ptbin not in tag: continue

        jetPtMin, jetPtMax = jetPtBins[ptbin][0], jetPtBins[ptbin][1]

        if 'Light' not in tag:

            binEventCut = andCuts([ 'muonJetPt>='+jetPtMin, 'muonJetPt<'+jetPtMax ])

            if 'Kinematics' in tag:

                cuts[ptbin] = binEventCut

            elif 'Templates' in tag:

                cuts[ptbin] = { 'expr' : binEventCut, 'categories' : {} }

                if 'System8' in tag: 
                    cuts[ptbin]['categories']['inclusive'] = 'true'
                    cuts[ptbin+'_AwayJetTag'] = { 'expr' : andCuts([ binEventCut, 'awayJetBTagSelection' ]) } 
                    cuts[ptbin+'_AwayJetTag']['categories'] = { 'inclusive' : 'true' } 

                for bTagAlgo in bTagAlgorithms:
                    bTagDiscriminant = bTagAlgorithms[bTagAlgo]
                    for wpName in workingPointName:

                        bTagWP = bTagAlgo+''.join([ x for x in wpName if x.isupper() ])
                        if bTagWP in bTagWorkingPoints:

                            bTagWPCut = 'Jet_'+bTagDiscriminant+'[muonJetIndex]>='+bTagWorkingPoints[bTagWP]

                            if 'PtRel' in tag:
                                cuts[ptbin]['categories'][bTagWP+'_Pass'] = bTagWPCut
                                cuts[ptbin]['categories'][bTagWP+'_Fail'] = bTagWPCut.replace('>=','<')
 
                            elif 'System8' in tag:
                                cuts[ptbin]['categories'][bTagWP] = bTagWPCut
                                cuts[ptbin+'_AwayJetTag']['categories'][bTagWP] = bTagWPCut

        else: 

            cuts[ptbin] = { 'expr' : andCuts([ binTriggerCut ]) }

            cuts[ptbin]['lightJetWeight']   = orCuts([lightAwayJetTrgSel, getPtHatSafetySelection() ], '*')
            lightTrkJetSel, nLightTrkJetCut = getMuonKinSelection(muonKinSelection)
            cuts[ptbin]['cutNLightTrkJet']  = nLightTrkJetCut

            if 'LightTemplates' in tag:

                cuts[ptbin]['cutLightTrkJetSel'] = lightTrkJetSel

### Set preselections

preselections = andCuts(preselectionList, True)


