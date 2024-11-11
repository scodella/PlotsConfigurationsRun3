# nuisances = {}









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

