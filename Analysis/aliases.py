import os
import json
import datetime
from array import array

aliases = {}
aliases = OrderedDict()

dataDir = '/'.join([ os.path.abspath('Data'), campaign ])
macrosPath = os.path.abspath('macros')

mc   = [ x for x in samples if not samples[x]['isDATA'] ]
data = [ x for x in samples if samples[x]['isDATA'] ]

## Preselections

aliases['goodPV'] = { 'expr' : 'PV_chi2<100.', 'samples': mc+data }

## Pileup reweighting

if len(mc)>0:

    if 'NoPU' not in tag and 'Validation' not in tag:

        aliases['pileupWeight'] = { 'linesToAdd': [ '#include "%s/pileupWeightsReader.cc+"' % macrosPath,
                                                    'PileupWeightsReader pileupWeight = PileupWeightsReader("'+dataDir+'/Pileup/pileupWeights_'+campaignRunPeriod['period']+'.root");' ],
                                    'expr': 'pileupWeight(nPUtrue)',
                                    'samples': mc
                                    }

        for sample in mc: samples[sample]['weight'] += '*pileupWeight[1]'

## Trigger infos

triggerInfosJSON = os.path.abspath(configsFolder) + '/' + '_'.join([ 'triggerInfos', year, tag, datetime.datetime.now().strftime('%y-%m-%d_%H_%M_%S') ]) + '.json'
with open(triggerInfosJSON, 'w') as file: file.write(json.dumps(triggerInfos))

## Kinematic weight list

kinematicWeightList = [] if '.' not in tag else [ tag.split('.',1)[-1].replace('.'+tag.split('.',1)[-1].split('.',x)[x],'') for x in range(len(tag.split('.'))-1) ]

## WorkingPoints

if 'WorkingPoints' in tag: 

    goodJetForDisc = '(('+jetPt+'>=30.)*(abs(Jet_eta)<'+maxJetEta+')*(Jet_hadronFlavour==JETFLV)*(Jet_tightID))'
    jetDisc = '(999999.*(!('+goodJetForDisc+')) + '+goodJetForDisc+'*(Jet_BTAGDISC))'

    for btagalgo in bTagAlgorithms:

        discriminantBins = (20000, 0., 20.) if 'JBP' in btagalgo else (11000, 0., 1.1)

        for flv in [ '0', '5' ]:

            bTagDiscriminantAlias = '_'.join([ 'Jet', bTagAlgorithms[btagalgo], flv ])
            aliases[bTagDiscriminantAlias] = { 'expr' : jetDisc.replace('BTAGDISC',bTagAlgorithms[btagalgo]).replace('JETFLV',flv),
                                               'samples' : mc,
                                               'discriminantBins' : discriminantBins,
                                               'xaxis' : 'Jet '+bTagAlgorithms[btagalgo]
                                               }

## BTagMu shapes

elif 'Light' not in tag:

    ## Soft muon and muon-jet variables

    aliases['softMuonIndex'] = { 'linesToAdd': [ '#include "%s/softMuonFinder.cc+"' % macrosPath ],
                                 'class': 'SoftMuonFinder',
                                 'args': 'nPFMuon,nJet,PFMuon_pt,PFMuon_eta,PFMuon_GoodQuality,PFMuon_IdxJet,'+mustBeUnique,
                                 'samples': mc+data
                                 }

    aliases['softMuonPt']    = { 'expr' : 'PFMuon_pt[softMuonIndex]',
                                 'samples': mc+data
                                 }

    aliases['softMuonEta']   = { 'expr' : 'PFMuon_eta[softMuonIndex]',
                                 'samples': mc+data
                                 }

    aliases['softMuonPhi']   = { 'expr' : 'PFMuon_phi[softMuonIndex]',
                                 'samples': mc+data
                                 }

    aliases['softMuonPtRel'] = { 'expr' : 'PFMuon_ptrel[softMuonIndex]',
                                 'samples': mc+data
                                 }

    aliases['muonJetIndex']  = { 'expr' : '((softMuonIndex>=0)*(PFMuon_IdxJet[softMuonIndex]))',
                                 'samples': mc+data
                                }

    aliases['muonJetPt']     = { 'expr' : jetPt+'[muonJetIndex]',
                                 'samples': mc+data
                                 }

    aliases['muonJetEta']    = { 'expr' : 'Jet_eta[muonJetIndex]',
                                 'samples': mc+data
                                 }

    aliases['muonJetPhi']    = { 'expr' : 'Jet_phi[muonJetIndex]',
                                 'samples': mc+data
                                 }
 
    aliases['muonJetDR']     = { 'expr' : 'sqrt(acos(cos(softMuonPhi-muonJetPhi))*acos(cos(softMuonPhi-muonJetPhi))+(softMuonEta-muonJetEta)*(softMuonEta-muonJetEta))',
                                 'samples': mc+data
                                 }
                                  
    # soft-muon and muon-jet selections

    aliases['softMuonSelection'] = { 'linesToAdd': [ '#include "%s/softMuonSelector.cc+"' % macrosPath,
                                                     'SoftMuonSelector softMuonSelection = SoftMuonSelector('+softMuonSelectionArgs+');' ],
                                     'expr': 'softMuonSelection(softMuonIndex, muonJetPt, softMuonPt, muonJetDR)',
                                     'samples': mc+data
                                     }
    
    muonJetSelList = [ 'muonJetPt>='+str(minJetPt), 'muonJetPt<'+str(maxJetPt), 'Jet_tightID[muonJetIndex]==1', 'abs(muonJetEta)<='+maxJetEta ]
    aliases['muonJetSelection']  = { 'expr' : ' && '.join(muonJetSelList),
                                     'samples': mc+data
                                     }

    ## Trigger selection

    aliases['triggerSelection'] = { 'linesToAdd': [ '#include "%s/triggerSelector.cc+"' % macrosPath,
                                                    'TriggerSelector triggerSelection = TriggerSelector("'+triggerInfosJSON+'","BTagMu",'+applyTriggerEmulation+','+maxJetEta+');' ],
                                    'expr': 'triggerSelection(muonJetIndex,nJet,'+jetPt+',Jet_eta,Jet_tightID,BitTrigger)',
                                    'samples': mc+data
                                    }

    ## Away-jet selection

    aliases['awayJetSelection'] = { 'linesToAdd': [ '#include "%s/awayJetSelector.cc+"' % macrosPath,
                                                    'AwayJetSelector awayJetSelection = AwayJetSelector("'+triggerInfosJSON+'",'+awayJetSelectionArgs+');' ],
                                    'expr': 'awayJetSelection(muonJetIndex,nJet,'+jetPt+',Jet_eta,Jet_phi,Jet_tightID,Jet_'+btagAwayJetDiscriminant+')',
                                    'samples': mc+data
                                    }

    if 'System8Templates' in method:

        aliases['awayJetBTagSelection'] = { 'linesToAdd': [ 'AwayJetSelector awayJetBTagSelection = AwayJetSelector("'+triggerInfosJSON+'",'+awayJetBTagSelectionArgs+');' ],
                                            'expr': 'awayJetBTagSelection(muonJetIndex,nJet,'+jetPt+',Jet_eta,Jet_phi,Jet_tightID,Jet_'+btagAwayJetDiscriminant+')',
                                            'samples': mc+data
                                            }

    ## Trigger prescales

    if len(data)>0:

        if 'NoPS' not in tag and 'Validation' not in tag:

            aliases['prescaleWeight'] = { 'linesToAdd': [ '#include "%s/triggerPrescalesReader.cc+"' % macrosPath,
                                                          'TriggerPrescalesReader prescaleWeight = TriggerPrescalesReader("'+triggerInfosJSON+'","BTagMu","'+dataDir+'/Prescales/Prescales_'+campaignRunPeriod['period']+'_HLT_BTagMu.json");' ],
                                          'expr': 'prescaleWeight(muonJetPt, Run, LumiBlock)',
                                          'samples': data
                                          }

            for sample in data: samples[sample]['weight'] += '*prescaleWeight'

    ## Kinematic weights

    if len(mc)>0:

        for kinematicWeight in kinematicWeightList:

            weightFile = dataDir+'/Kinematics/'+'.'.join([ method+'_QCDMu', kinematicWeight, 'root' ])
            weightName = kinematicWeight.split('.')[-1]
            aliases[weightName] = { 'linesToAdd': [ '#include "%s/kinematicWeightsReader.cc+"' % macrosPath,
                                                    'KinematicWeightsReader '+weightName+' = KinematicWeightsReader("'+weightFile+'","'+weightName+'");' ],
                                    'expr': weightName+'(muonJetPt,muonJetEta)',
                                    'samples': mc
                                    }

            for sample in mc: samples[sample]['weight'] += '*'+weightName

    ## MC templeates specific aliases

    if 'Templates' in tag and len(mc)>0:

        # Generation weights

        aliases['muonJetGenPt']    = { 'expr' : 'Jet_genpt[muonJetIndex]', 'samples': mc }
        aliases['muonJetFlavour']  = { 'expr' : 'Jet_hadronFlavour[muonJetIndex]', 'samples': mc }

        aliases['muonJetFromB']    = { 'expr' : '(muonJetFlavour==5)', 'samples': mc }
        aliases['muonJetFromC']    = { 'expr' : '(muonJetFlavour==4)', 'samples': mc }
        aliases['muonJetFromL']    = { 'expr' : '(muonJetFlavour<4)',  'samples': mc }
        aliases['muonJetNotFromB'] = { 'expr' : '(muonJetFlavour!=5)', 'samples': mc }

        # JEU

        aliases['muonJetPt_jeuUp']   = { 'linesToAdd': [ '#include "%s/jetEnergyUncertaintyReader.cc+"' % macrosPath,
                                                         'JetEnergyUncertaintyReader jetEnergyCorrector = JetEnergyUncertaintyReader("'+dataDir+'/JEU/'+jetEnergyUncertaintyFile+'");' ],
                                          'expr': 'jetEnergyCorrector(nJet,muonJetPt,muonJetEta,"Up")',
                                          'samples': mc
                                          }

        aliases['muonJetPt_jeuDown'] = {  'expr': 'jetEnergyCorrector(nJet,muonJetPt,muonJetEta,"Down")',
                                          'samples': mc
                                          }

        if 'bjets' in mc and 'Validation' not in tag:

            # Gluon splitting

            BHadronDeltaPhi  = 'acos(cos(BHadron_phi-muonJetPhi))'
            BHadronDeltaEta  = '(BHadron_eta-muonJetEta)'
            BHadronDeltaR    = 'sqrt('+BHadronDeltaPhi+'*'+BHadronDeltaPhi+'+'+BHadronDeltaEta+'*'+BHadronDeltaEta+')'
            aliases['isGluonSplitting'] = { 'expr' : '(Sum('+BHadronDeltaR+'<=0.4 && BHadron_hasBdaughter==0)>=2)', 'samples': [ 'bjets' ] }

            # b fragmentation

            aliases['bHadronWeight'] = { 'linesToAdd': [ '#include "%s/bFragmentationWeightsReader.cc+"' % macrosPath,
                                                         'BFragmentationWeightsReader bHadronWeight = BFragmentationWeightsReader("'+bfragweightFile+'","'+fragTune+'","'+bdecayweightsFile+'");' ],
                                         'expr': 'bHadronWeight(muonJetIndex,muonJetFlavour,muonJetEta,muonJetPhi,muonJetGenPt,nBHadron,BHadron_pT,BHadron_eta,BHadron_phi,BHadron_mass,BHadron_pdgID,BHadron_hasBdaughter)',
                                         'samples': [ 'bjets' ]
                                         }

            if applyBFragmentation>=2: samples['bjets']['weight'] += '*bHadronWeight[1]'

## Light shapes

else:

    pass
    # pthat safety selection

    #aliases['ptHatSafetySelection'] = { 'expr' : 'pthat<100.',
    #                                    'samples': mc
    #                                    }

    #for sample in mc: samples[sample]['weight'] += '*ptHatSafetySelection'


