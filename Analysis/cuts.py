##### cuts = {}

def andCuts(cutList):
    return ' && '.join(cutList)

def orCuts(cutList, operator = ' || '):
    return '(' + operator.join([ '('+x+')' for x in cutList ]) + ')'

