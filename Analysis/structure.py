# structure configuration for datacard

#structure = {}

# keys here must match keys in samples.py   

for sample in samples:

    structure[sample] = {
                  'isSignal' : samples[sample]['isSignal'],
                  'isData'   : samples[sample]['isDATA']
    }
 
    if 'removeFromCuts' in samples[sample]:
        structure[sample]['removeFromCuts'] = samples[sample]['removeFromCuts']

