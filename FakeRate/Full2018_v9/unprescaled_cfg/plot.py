# plot configuration

# Groups of samples to improve the plots.
# If not defined, normal plots is used

# lepton_categories = ['_ele_low_pt', '_ele_high_pt', '_muon_low_pt', '_muon_high_pt']

groupPlot = {}

groupPlot['DY']  = {  
    'nameHR'   : "DY",
    'isSignal' : 0,
    'color'    : 418, # kGreen+2
    'samples'  : ['DY_unprescaled']
}

# groupPlot['WJets']  = {  
#     'nameHR'   : "WJets",
#     'isSignal' : 0,
#     'color'    : 11, # kGrey
#     'samples'  : ['WJets' + lep_cat for lep_cat in lepton_categories]
# }

plot = {}

# for lep_cat in lepton_categories:

plot['DY_unprescaled']  = {  
    'nameHR'   : 'DY',
    'color'    : 418, # kGreen+2
    'isSignal' : 0,
    'isData'   : 0, 
    'scale'    : 1.0,
}

    # plot['WJets' + lep_cat] = {   
    #     'nameHR' : 'WJets',
    #     'color'    : 11, # kGrey
    #     'isSignal' : 0,
    #     'isData'   : 0, 
    #     'scale'    : 1.0,
    # }

########
# Data #
########

plot['DATA_unprescaled']  = { 
    'nameHR'   : 'Data',
    'color'    : 1 ,  
    'isSignal' : 0,
    'isData'   : 1,
    'isBlind'  : 0
}


# Define legend

legend = {}

legend['lumi'] = 'L = 59.8 fb^{-1}'
legend['sqrt'] = '#sqrt{s} = 13 TeV'
