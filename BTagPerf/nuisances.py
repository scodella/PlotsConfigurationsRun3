nuisances = {}

# statistical uncertainty

nuisances['stat']  = { 'type'          : 'auto', # Use the following if you want to apply the automatic combine MC stat nuisances.
                       'maxPoiss'      : '10',   # Number of threshold events for Poisson modelling
                       'includeSignal' : '1',    # Include MC stat nuisances on signal processes (1=True, 0=False)
                       'samples'       : {}
                      }

if 'Templates' in tag:

    # pileup
    if 'pileup' in systematicNuisances:
        nuisances['pileup']  = { 'name'    : 'pileup',
                                 'kind'    : 'weight',
                                 'type'    : 'shape',
                                 'samples' : dict((skey, [ 'pileupWeight[2]/pileupWeight[1]', 'pileupWeight[0]/pileupWeight[1]' ]) for skey in mc),
                                }

    # JEU
    if 'jeu' in systematicNuisances:
        nuisances['jeu'] = { 'name'       : 'jeu',
                             'kind'       : 'suffix',
                             'type'       : 'shape',
                             'mapUp'      : 'jeuUp',
                             'mapDown'    : 'jeuDown',
                             'samples'    : dict((skey, ['1', '1']) for skey in mc),
                             'folderUp'   : '',
                             'folderDown' : '',
                            }

    # b specific nuisances
    if 'bjets' in samples:

        # gluon splitting
        if 'gluonSplitting' in systematicNuisances:
            nuisances['gluonSplitting']  = { 'name'  : 'gluonSplitting',
                                             'samples'  : { 'bjets' : [ '1.5*isGluonSplitting+(!(isGluonSplitting))', '0.5*isGluonSplitting+(!(isGluonSplitting))' ] },
                                             'kind'  : 'weight',
                                             'type'  : 'shape'
                                            }

        # b hadron fragmentation
        if 'bfragmentation' in systematicNuisances:
            nuisances['bfragmentation']  = { 'name'  : 'bfragmentation',
                                             'samples'  : { 'bjets' : [ 'bHadronWeight[2]/bHadronWeight[1]', 'bHadronWeight[0]/bHadronWeight[1]' ] },
                                             'kind'  : 'weight',
                                             'type'  : 'shape'
                                            }

        # b semileptonic decays' br
        if 'bdecay' in systematicNuisances:
            nuisances['bdecay']  = { 'name'  : 'bdecay',
                                     'samples'  : { 'bjets' : [ 'bHadronWeight[4]', 'bHadronWeight[3]' ] },
                                     'kind'  : 'weight',
                                     'type'  : 'shape'
                                    }

    # ptrel specific nuisances
    if 'PtRel' in method:

        # light specific nuisances
        if 'ljets' in samples and 'lightCharmRatio' in systematicNuisances:

            # light to charm ratio
            if 'ForFit' not in tag:

                nuisances['lightCharmRatio'] = { 'name'  : 'lightCharmRatio',
                                                 'samples'  : { 'ljets' : '1.3', },
                                                 'type'  : 'lnN'
                                                }

            elif '2D' in tag: 

                nuisances['lightCharmRatio'] = { 'name'  : 'lightCharmRatio',
                                                 'samples'  : { 'ljets' : [ '1.', '1.' ] },
                                                 'type'  : 'shape',
                                                 'kind'  : 'weight'
                                                }

        # nuisances for PtRel fits
        if 'ForFit' in tag:

            # template corrections
            for nuisance in templateCorrectionNuisances:

                nuisances[nuisance]  = { 'name'  : nuisance,
                                         'samples'  : { templateCorrectionNuisances[nuisance] : [ 1., 1. ] },
                                         'kind'  : 'weight',
                                         'type'  : 'shape'
                                        }

            # decouple nuisances in simultaneous fits to all selections 
            if '_mergedSelections' in tag and '_nuisSelections' in tag:
                for selection in systematicVariations:
                    nuisance = selection.replace('Up','').replace('Down','')
                    if nuisance in nuisances and nuisance in systematicNuisances:
                        nuisances[nuisance]['cuts'] = []
                        for cut in cuts:
                            if nuisance not in cut:
                                nuisances[nuisance]['cuts'].append(cut)
                        
            # rate parameters
            for cut in cuts:
                for sample in samples:
                    if not samples[sample]['isDATA']:

                        if sample=='bjets' and '_nobRP' in tag: continue

                        nuisances[sample+'_'+cut]  = { 'name'    : sample+'_'+cut,
                                                       'type'    : 'rateParam',
                                                       'samples' : { sample : '1.' },
                                                       'cuts'    : [ cut ]
                                                      }

                        if 'AwayJet888' not in cut or 'Pass' in cut or not samples[sample]['isSignal'] or '_NoAwayJetBond' in tag:
   
                            nuisances[sample+'_'+cut]['limits'] = '[0.01,20]'

                        else:

                            fileIn = ROOT.TFile(inputFile, 'READ')

                            nuisances[sample+'_'+cut]['bond'] = {}
                            nuisances[sample+'_'+cut]['bond'][cut] = {}

                            for variable in variables:
                                if 'cuts' not in variables[variable] or cut in variables[variable]['cuts']:

                                    awayJetFailCut   = cut
                                    awayJetPassCut   = cut.replace('Fail','Pass')
                                    muonJetFailCut   = cut.replace('_AwayJetUp','').replace('_AwayJetDown','')
                                    muonJetPassCut   = muonJetFailCut.replace('Fail','Pass')

                                    awayJetFailHisto = fileIn.Get(awayJetFailCut+'/'+variable+'/histo_'+sample)
                                    awayJetPassHisto = fileIn.Get(awayJetPassCut+'/'+variable+'/histo_'+sample)
                                    muonJetFailHisto = fileIn.Get(muonJetFailCut+'/'+variable+'/histo_'+sample)   
                                    muonJetPassHisto = fileIn.Get(muonJetPassCut+'/'+variable+'/histo_'+sample)                            

                                    awayJetFailYield = awayJetFailHisto.Integral()
                                    awayJetPassYield = awayJetPassHisto.Integral()
                                    muonJetFailYield = muonJetFailHisto.Integral()
                                    muonJetPassYield = muonJetPassHisto.Integral()
  
                                    awayJetFailRelativeYield = awayJetFailYield/(awayJetFailYield+awayJetPassYield)
                                    awayJetPassRelativeYield = awayJetPassYield/(awayJetFailYield+awayJetPassYield)
                                    muonJetFailRelativeYield = muonJetFailYield/(muonJetFailYield+muonJetPassYield)
                                    muonJetPassRelativeYield = muonJetPassYield/(muonJetFailYield+muonJetPassYield)
 
                                    differencePassRelativeYields = str(muonJetPassRelativeYield-awayJetPassRelativeYield)
                                    muonJetFailFactor = '(@1/@0)*'+str(muonJetFailRelativeYield)
                                    awayJetFailFactor = '@2/'+str(awayJetFailRelativeYield)

                                    bond_formula = '(('+differencePassRelativeYields+'+'+muonJetFailFactor+')*'+awayJetFailFactor+') '
                                    bond_parameters = ','.join([ sample+'_'+muonJetPassCut, sample+'_'+muonJetFailCut, sample+'_'+awayJetPassCut  ])

                                    nuisances[sample+'_'+cut]['bond'][cut][variable] = { bond_formula : bond_parameters }

                            fileIn.Close()

### Cleaning

nuisanceToRemove = [ ]

for nuisance in list(nuisances.keys()):

    if len(nuisances[nuisance]['samples'].keys())==0:
        nuisanceToRemove.append(nuisance)

    if 'cuts' in nuisances[nuisance]:
        if len(nuisances[nuisance]['cuts'])==0:
            nuisanceToRemove.append(nuisance)

for nuisance in nuisanceToRemove:
    if nuisance in nuisances: del nuisances[nuisance]

