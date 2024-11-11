#!/usr/bin/env python
import timeit
import optparse
import sys  
import os
import math
import ROOT
import LatinoAnalysis.Gardener.hwwtools as hwwtools
from collections import OrderedDict

def getSampleYields(sample, shape, nBins, SMyields):

    sampleYields = ''
    maxYields, maxSignificance = 0., 0.
    for ibin in range(1, nBins+1):
        yields = shape.GetBinContent(ibin)
        error = shape.GetBinError(ibin)  
        if yields>=maxYields:
            maxYields = yields 
        if len(SMyields)>0 and yields>0.:
            if yields/math.sqrt(yields+SMyields[ibin-1])>maxSignificance:
                maxSignificance = yields/math.sqrt(yields+SMyields[ibin-1])
        if yields>=100.:
            yieldsString = '%.0f' % yields
            errorString = '%.0f' % error
        elif yields>=1.:
            yieldsString = '%.1f' % yields
            errorString = '%.1f' % error
        else:
            yieldsString = '%.2f' % yields
            errorString = '%.2f' % error  
        sampleYields += ' & $' + yieldsString + '\\pm ' + errorString +'$'

    return sampleYields, maxYields, maxSignificance

if __name__ == '__main__':

    usage = 'usage: %prog [options]'
    parser = optparse.OptionParser(usage)

    parser.add_option('--inputDir'        , dest='inputDir'        , help='Intput directory from shapes'           , default='./Shapes')
    parser.add_option('--inputDirMaxFit'  , dest='inputDirMaxFit'  , help='Intput directory from fit'              , default='./MaxLikelihoodFits')
    parser.add_option('--outputTableDir'  , dest='outputTableDir'  , help='Output directory for the tables'        , default='./Tables')
    parser.add_option('--tag'             , dest='tag'             , help='Tag used for the tag file name'         , default='test')
    parser.add_option('--year'            , dest='year'            , help='Year in the fit'                        , default='test')    
    parser.add_option('--masspoints'      , dest='masspoints'      , help='Masspoints'                             , default=[])
    parser.add_option('--fit'             , dest='fit'             , help='Fit level'                              , default='prefit')
    parser.add_option('--cardName'        , dest='cardName'        , help='Card name structure'                    , default='cut')
    parser.add_option('--unblind'         , dest='unblind'         , help='Unblind data'                           , default=False, action='store_true')
    parser.add_option('--nosignal'        , dest='nosignal'        , help='Do not write signal yields'             , default=False, action='store_true')
    parser.add_option('--fromshapes'      , dest='fromshapes'      , help='Use processe shapes'                    , default=False, action='store_true')
    parser.add_option('--mergedyears'     , dest='mergedyears'     , help='mergedyears'                            , default=False, action='store_true')
    parser.add_option('--maxsignallines'  , dest='maxsignallines'  , help='Maximum number of lines for signals'    , default=5)
    parser.add_option('--minsignalyields' , dest='minsignalyields' , help='Minimal signal yields for tables'       , default=0.6)
    parser.add_option('--minsignalsig'    , dest='minsignalsig'    , help='Minimal signal significance for tables' , default=0.5)
    # read default parsing options as well
    hwwtools.addOptions(parser)
    hwwtools.loadOptDefaults(parser)
    (opt, args) = parser.parse_args()
 
    os.system('mkdir -p '+opt.outputTableDir)

    inputFiles = { }
    if opt.fromshapes:
        opt.sigset = 'SM-'+opt.masspoints
        refmasspoint = opt.masspoints
        for masspoint in opt.masspoints.split(','):
            inputFiles[masspoint] = ROOT.TFile(opt.inputDir+'/plots_'+opt.tag+'_SM-'+masspoint+'.root', 'READ')
    else:
        if opt.masspoints=='':
            inputFiles['SM'] = ROOT.TFile(opt.inputDirMaxFit+'/fitDiagnostics.root', 'READ')
            refmasspoint = 'SM' 
            opt.sigset = 'SM'
        else:
            opt.sigset = 'SM-'+opt.masspoints
            for masspoint in opt.masspoints.split(','):
                if masspoint=='TChipmSlepSnu_mC-1150_mX-1':
                    if os.path.isfile('/'.join([ './MaxLikelihoodFits/2016-2017-2018/CharginoSignalRegionsMergeWWPol1aGroupSmtEUFitCRVetoesULSigV6_NewBond3', masspoint, 'fitDiagnostics.root' ])):
                       inputFiles[masspoint] = ROOT.TFile('/'.join([ './MaxLikelihoodFits/2016-2017-2018/CharginoSignalRegionsMergeWWPol1aGroupSmtEUFitCRVetoesULSigV6_NewBond3', masspoint, 'fitDiagnostics.root' ]))
                       refmasspoint = masspoint
                elif masspoint=='T2tt_mS-525_mX-438': 
                    if os.path.isfile('/'.join([ 'MaxLikelihoodFits/2016-2017-2018/StopSignalRegionsFXbtvWWPol1aGroupSmtEUFitCRVetoesULFast_NewBond2', masspoint, 'fitDiagnostics.root' ])):
                       inputFiles[masspoint] = ROOT.TFile('/'.join([ './MaxLikelihoodFits/2016-2017-2018/StopSignalRegionsFXbtvWWPol1aGroupSmtEUFitCRVetoesULFast_NewBond2', masspoint, 'fitDiagnostics.root' ]))
                       refmasspoint = masspoint
                else:
                    if os.path.isfile('/'.join([ opt.inputDirMaxFit, masspoint, 'fitDiagnostics.root' ])):
                        inputFiles[masspoint] = ROOT.TFile('/'.join([ opt.inputDirMaxFit, masspoint, 'fitDiagnostics.root' ]), 'READ')
                        #refmasspoint = masspoint 

    opt.tag = opt.year+opt.tag
    samples = { }
    cuts = { }
    variables = { }
    plot = OrderedDict()
    groupPlot = { }
    legend = { }

    exec(open(opt.samplesFile).read())
    exec(open(opt.cutsFile).read())
    exec(open(opt.variablesFile).read())
    exec(open(opt.plotFile).read())

    samples['total_background'] = { 'isData' : 0, 'isSignal' : 0 }
    plot['total_background'] = { 'isData' : 0, 'isSignal' : 0, 'nameHR' : 'SM Processes' }

    if refmasspoint=='SM':
        for sample in list(plot.keys()):
            if plot[sample]['isSignal']:
                plot[sample]['isSignal'] = 0

    yearList = opt.year if opt.mergedyears else opt.year.split('-')

    for fittype in opt.fit.split('-'):
        for year in yearList:
            for cut in cuts:
                for variable in variables:
                    if 'cuts' not in variables[variable] or cut in variables[variable]['cuts']:

                        cardName = opt.cardName.replace('year', year).replace('cut', cut).replace('variable', variable)

                        if opt.fromshapes:
                            histoprefix = 'histo_'
                            inDir = '/'.join([ cut, variable ])
                        else:
                            histoprefix = ''
                            inDir = 'shapes_'+fittype.lower().replace('postfit','_fit_') + '/' + cardName
                            inDirRef = 'shapes_'+fittype.lower().replace('postfit','_fit_') + '/' + cardName + '_' + year
                        #if not inputFiles[refmasspoint].GetListOfKeys().Contains(inDir):
                        #    print 'warning: missing directory', inDir, 'in', inputFiles[refmasspoint].GetName()
                        #    continue
                        if 'CR' in inDir: continue

                        if len(variables[variable]['range'])<=2: nBins = len(variables[variable]['range'][0])-1
                        elif len(variables[variable]['range'])==3: nBins = variables[variable]['range'][0]

                        tableName = opt.outputTableDir+'/Yields_'+fittype+'_'+cardName+'.tex'
                        table = open(tableName , 'w')

                        #table.write('\\begin{center}\n')
                        table.write('\\begin{tabular}{l')
                        for ibin in range(nBins): table.write('c')
                        table.write('}\n')

                        table.write('\\hline\n')

                        table.write(variables[variable]['nameLatex']+' bin')
                        if len(variables[variable]['range'])<=2:           
                            variableEdges = variables[variable]['range'][0]
                        elif len(variables[variable]['range'])==3:
                            binWidth = (variables[variable]['range'][2]-variables[variable]['range'][1])/variables[variable]['range'][0]
                            for ibin in range(nBins): variableEdges[ibin] = variables[variable]['range'][1]+ibin*binWidth                              
                        for ibin in range(nBins-1):
                            table.write(' & '+str(variableEdges[ibin])+'-'+str(variableEdges[ibin+1]))
                        table.write(' & $\\ge '+str(variableEdges[nBins-1])+'$')

                        table.write(' \\\\\n')
                   
                        refDir = inputFiles[refmasspoint].Get(inDirRef)
                     

                        SMyields = [ ]
                        signalPoint = [ ]
                        signalYields = { }
                        signalMaximum = { }
                        signalSignificance = { } 

                        for iteration in range(4):
                            if (iteration!=2 or opt.unblind) and (iteration!=3 or not opt.nosignal): table.write('\\hline\n')
                            for sample in list(plot.keys()):

                                if iteration==0 and (plot[sample]['isData'] or plot[sample]['isSignal'] or sample=='total_background'): continue
                                if iteration==1 and sample!='total_background': continue
                                if iteration==2 and (not plot[sample]['isData'] or not opt.unblind): continue 
                                if iteration==3 and (not plot[sample]['isSignal'] or opt.nosignal): continue

                                sampleName = 'data' if plot[sample]['isData'] else sample
                                if plot[sample]['isSignal']:
                                    if sample in inputFiles:
                                        shape = inputFiles[sample].Get(inDir+'/'+histoprefix+sample)
                                    else: continue
                                elif plot[sample]['isData'] and not opt.fromshapes:
                                    graph = refDir.Get('data')
                                    shape = ROOT.TH1F('shape', '', graph.GetN(), 0, graph.GetN())
                                    for ipoint in range(0, graph.GetN()):
                                        shape.SetBinContent(int(graph.GetX()[ipoint])+1, graph.GetY()[ipoint])
                                        shape.SetBinError(int(graph.GetX()[ipoint])+1,  graph.GetErrorY(ipoint))
                                else:
                                    if refDir.GetListOfKeys().Contains(histoprefix+sample):
                                        shape = refDir.Get(histoprefix+sample)
                                    else: continue

                                if shape:
                                    sampleName = plot[sample]['nameLatex'] if 'nameLatex' in plot[sample] else plot[sample]['nameHR']
                                    sampleYields, maxYields, maxSignificance = getSampleYields(sample, shape, nBins, SMyields)

                                    if iteration!=3:
                                        table.write(sampleName+sampleYields+' \\\\\n')
                                        if iteration==1:
                                            for ibin in range(1, nBins+1):
                                                SMyields.append(shape.GetBinContent(ibin))

                                    elif maxYields>opt.minsignalyields and maxSignificance>opt.minsignalsig:
                                        signalPoint.append(sampleName)
                                        signalYields[sampleName] = sampleYields             
                                        signalMaximum[sampleName] = maxYields
                                        signalSignificance[sampleName] = maxSignificance
 
                        for s1 in range(len(signalPoint)):
                            for s2 in range(s1+1, len(signalPoint)):
                                #if signalMaximum[signalPoint[s2]]>signalMaximum[signalPoint[s1]]:
                                if signalSignificance[signalPoint[s2]]>signalSignificance[signalPoint[s1]]:
                                    saveSignalName = signalPoint[s1]
                                    signalPoint[s1] = signalPoint[s2]
                                    signalPoint[s2] = saveSignalName

                        for siter in range(len(signalPoint)):
                            if siter<opt.maxsignallines:
                                table.write(signalPoint[siter]+signalYields[signalPoint[siter]]+' \\\\\n')

                        table.write('\\hline\n')

                        table.write('\\end{tabular}\n')
                        #table.write('\\end{center}\n') 
                             

