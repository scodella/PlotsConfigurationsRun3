nuisances = {}

# statistical uncertainty

nuisances['stat']  = { 'type'          : 'auto', # Use the following if you want to apply the automatic combine MC stat nuisances.
                       'maxPoiss'      : '10',   # Number of threshold events for Poisson modelling
                       'includeSignal' : '1',    # Include MC stat nuisances on signal processes (1=True, 0=False)
                       'samples'       : {}
                      }

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

