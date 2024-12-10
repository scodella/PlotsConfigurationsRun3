# Flags  
gv    = ' [GeV]'
pt    = '#font[50]{p}_{T}'
met   = pt+'^{miss}'
ptrel = pt+'^{rel}'
sll   = '#font[12]{ll}'
pll   = '('+sll+')'
mt2   = '#font[50]{m}_{T2}'
ptll  = pt+'^{'+sll+'}'

overflow  = 2
underflow = 1

variables = {}

jetEtaBins = ( int(2*float(maxJetEta)/0.1) , -float(maxJetEta), float(maxJetEta) )
# This does not work in python3
#jetEta2DBins = [ -float(maxJetEta)+edge*0.1 for edge in range(int(2*float(maxJetEta)/0.1)+1) ]
jetEta2DBins = [ edge*0.1 for edge in range(int(-float(maxJetEta)/0.1), int(float(maxJetEta)/0.1)+1) ]

if 'WorkingPoints' in tag:

    for bTagDiscriminantAlias in aliases:
        if 'discriminantBins' in aliases[bTagDiscriminantAlias]:

            variables[bTagDiscriminantAlias] = { 'name'  : bTagDiscriminantAlias,
                                                 'range' : aliases[bTagDiscriminantAlias]['discriminantBins'],
                                                 'xaxis' : aliases[bTagDiscriminantAlias]['xaxis']
                                                }

elif method+'Kinematics' in tag:

    variables['mujeteta']        = { 'name'  : 'muonJetEta',
                                     'range' : jetEtaBins,
                                     'xaxis' : '#mu-jet pseudorapodity',
                                    }

    variables['muonpt']          = { 'name'  : 'muonJetPt',
                                     'range' : (25, 5., 30.),
                                     'xaxis' : '#mu '+pt+gv,
                                     'fold'  : overflow
                                    }

    variables['PV']              = { 'name'  : 'npvsGood',
                                     'range' : (50, 0., 50.),
                                     'xaxis' : 'number of good PVs',
                                     'fold'  : overflow
                                    }

    for cut in cuts:

        jetPtMin, jetPtMax = float(jetPtBins[cut][0]), float(jetPtBins[cut][1])
        muJetPtBins  = ( int(jetPtMax-jetPtMin), jetPtMin, jetPtMax )

        muJetPt2DBins = [ ]
        for edge in range(int(jetPtMin), int(jetPtMax)+1):
            muJetPt2DBins.append(edge)

        variables['mujetpt_'+cut]         = { 'name'  : 'muonJetPt',
                                              'range' : muJetPtBins,
                                              'xaxis' : '#mu-jet '+pt+gv,
                                              'cuts'  : [ cut ]
                                              }

        #variables['mujetpteta_'+cut]      = { 'name'  : 'muonJetEta:muonJetPt',
        #                                      'range' : (muJetPt2DBins, jetEta2DBins),
        #                                      'xaxis' : '2D #mu-jet eta:'+pt,
        #                                      'cuts'  : [ cut ]
        #                                     }

elif method+'Templates' in tag:

    variables['ptrel'] = { 'name'  : 'softMuonPtRel',
                           'range' : ptRelRange,
                           'xaxis' : '#mu-jet '+ptrel+gv,
                           'fold'  : overflow
                           }




