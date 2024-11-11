# variables = {}

# Flags  
gv    = ' [GeV]'
pt    = '#font[50]{p}_{T}'
met   = pt+'^{miss}'
ptrel = pt+'^{rel}'
sll   = '#font[12]{ll}'
pll   = '('+sll+')'
mt2   = '#font[50]{m}_{T2}'
ptll  = pt+'^{'+sll+'}'

if hasattr(opt, 'batchQueue') and not hasattr(opt, 'dryRun'): ## mkShape
    overflow  = 1
    underflow = 2
else: ## mkShapeMulti
    overflow  = 2
    underflow = 1


