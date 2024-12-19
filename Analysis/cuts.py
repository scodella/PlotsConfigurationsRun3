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

preselections = 'true'



