# plot configuration

### General parameters

legend = {}
if lumi>100: lumi_i=int(round(lumi, 0))
else           : lumi_i=round(lumi, 1)
#legend['lumi'] = 'L = '+str(lumi_i)+'/fb'
legend['lumi'] = str(lumi_i)+' fb^{-1} '
legend['sqrt'] = '#sqrt{s} = '+CME+' TeV'

# CMS colour scheme
# https://gitlab.cern.ch/cms-analysis/analysisexamples/plotting-demo/-/blob/master/1-tutorial_CAT_recommendations.ipynb
# petroff6 = ListedColormap(["#5790fc", "#f89c20", "#e42536", "#964a8b", "#9c9ca1", "#7a21dd"])
# petroff10 = ListedColormap(["#3f90da", "#ffa90e", "#bd1f01", "#94a4a2", "#832db6", "#a96b59", "#e76300", "#b9ac70", "#717581", "#92dadd"])

### groupPlot = {}
# 
# Groups of samples to improve the plots.
# If not defined, normal plots is used
#

# ... your groupPlot here ...

### plot = {}
#
# keys here must match keys in samples.py    
#    

# ... your plot here ...

### samples and groups to be removed from plots               

sampleToRemoveFromPlot = [ ] 

for sample in plot:
    if sample not in samples:
        sampleToRemoveFromPlot.append(sample)

for sample in sampleToRemoveFromPlot:
    del plot[sample]

groupToRemoveFromPlot = [ ] 

for group in groupPlot:
    for sample in sampleToRemoveFromPlot:
        if sample in groupPlot[group]['samples']:
            groupPlot[group]['samples'].remove(sample)
    if len(groupPlot[group]['samples'])==0:
        groupToRemoveFromPlot.append(group)
    
for group in groupToRemoveFromPlot:
    del groupPlot[group]

### BSM signals

### cuts to be removed from group

for group in groupPlot:
    cutToRemoveFromGroup = [ ]
    for cut in cuts:
        samplesInCut = [ ]
        for sample in groupPlot[group]['samples']:
            if not ('removeFromCuts' in samples[sample] and cut in samples[sample]['removeFromCuts']):
                samplesInCut.append(sample)
        if len(samplesInCut)==0:
            cutToRemoveFromGroup.append(cut)
    if len(cutToRemoveFromGroup)>0:
        groupPlot[group]['removeFromCuts'] = cutToRemoveFromGroup
        




