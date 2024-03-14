
plot = {}

groupPlot = {}

groupPlot['WWewk_CMWW_LL']  = {  
    'nameHR' : 'VBS LL (CMWW)',
    'isSignal' : 1,
    'color'    : 800,   # kOrange
    'samples'  : ['WWewk_CMWW_LL'],
    #'drawNormalized': 1
}

groupPlot['WWewk_CMWW_LT']  = {  
    'nameHR' : 'VBS LT (CMWW)',
    'isSignal' : 1,
    'color'    : 802,   # kOrange + 2
    'samples'  : ['WWewk_CMWW_LT'],
    #'drawNormalized': 1
}

groupPlot['WWewk_CMWW_TL']  = {  
    'nameHR' : 'VBS TL (CMWW)',
    'isSignal' : 1,
    'color'    : 804,   # kOrange + 4
    'samples'  : ['WWewk_CMWW_TL'],
    #'drawNormalized': 1
}

groupPlot['WWewk_CMWW_TT']  = {  
    'nameHR' : 'VBS TT (CMWW)',
    'isSignal' : 1,
    'color'    : 806,   # kOrange + 6
    'samples'  : ['WWewk_CMWW_TT'],
    #'drawNormalized': 1
}

groupPlot['WW']  = {  
    'nameHR' : 'WW',
    'isSignal' : 0,
    'color'    : 851, # kAzure -9 
    'samples'  : ['WWjj_QCD', 'ggWW'],
    #'drawNormalized': 1
}

groupPlot['top']  = {  
                  'nameHR' : 'tW and t#bar{t}',
                  'isSignal' : 0,
                  #'color': 400,   # kYellow
                  'color': ROOT.kYellow,   # kYellow
                  'samples'  : ['top'],
                  #'drawNormalized': 1
}

groupPlot['Higgs']  = {  
                  'nameHR' : 'Higgs',
                  'isSignal' : 0,
                  'color': 632, # kRed 
		  'samples'  : ['qqH_hww', 'ggH_hww',]#'ttH_hww','ZH_htt', 'ggZH_htt', 'WH_htt', 'qqH_htt', 'ggH_htt','bbH_htt','ttH_htt' ]
              }

groupPlot['Fake']  = {
                  'nameHR' : 'nonprompt',
                  'isSignal' : 0,
                  'color': 921,    # kGray + 1
                  'samples'  : ['Fake_m', 'Fake_e']
}

groupPlot['Multiboson']  = {  
                  'nameHR' : 'Multiboson',
                  'isSignal' : 0,
                  'color': 617, # kViolet + 1  
                  #'samples'  : ['WWewk','WW', 'ggWW', 'VVV', 'VZ', 'WZ', 'ZZ', 'Vg', 'Wg', 'VgS_H', 'VgS_L']
                  'samples'  : ['Vg', 'VgS_H', 'VgS_L', 'VZ', 'VVV']
                  #'VVV', 'VZ', 'WZ', 'ZZ', 'Vg', 'Wg', 'VgS_H', 'VgS_L']
              }

groupPlot['Zjj']  = {  
                  'nameHR': 'Zjj',
                  'isSignal' : 0,
                  'color': 600,    # kBlue
                  'samples'    : ['Zjj']
              }

groupPlot['dy']  = {  
    'nameHR' : "DY",
    'isSignal' : 0,
    'color'    : 418,    # kGreen+2
    'samples'  : ['dytt', 'dyll']
}

groupPlot['DATA']  = { 
                  'nameHR' : 'Data',
                  'color': 1 ,  
                  'isSignal' : 0,
                  'isData'   : 1 ,
                  'isBlind'  : {
                      'VBS_2j_em_isVBS': 'full',
                      'VBS_2j_SF_isVBS': 'full',
                      }
              }

_mergedCuts = []
for cut in list(cuts.keys()):
    __cutExpr = ''
    if type(cuts[cut]) == dict:
        __cutExpr = cuts[cut]['expr']
        for cat in list(cuts[cut]['categories'].keys()):
            _mergedCuts.append(cut + '_' + cat)
    elif type(cuts[cut]) == str:
        _mergedCuts.append(cut)

cuts2j = _mergedCuts

plot['DATA']  = { 
                  'nameHR' : 'Data',
                  'color': 1 ,  
                  'isSignal' : 0,
                  'isData'   : 1 ,
                  'isBlind'  : 0,
                  'blind'   :  dict([(cut, 'full') for cut in cuts2j if 'isVBS' in cut])
              }
legend = {}
legend['lumi'] = 'L = 59.83 fb^{-1}'

legend['sqrt'] = '#sqrt{s} = 13 TeV'

