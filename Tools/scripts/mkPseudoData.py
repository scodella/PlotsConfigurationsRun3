#!/usr/bin/env python
import os
import sys
import ROOT
import math
import optparse
import LatinoAnalysis.Gardener.hwwtools as hwwtools

if __name__ == '__main__':

    usage = 'usage: %prog [options]'
    parser = optparse.OptionParser(usage)

    parser.add_option('--inputDir'       , dest='inputDir'       , help='Input directory'              , default='./Shapes')
    parser.add_option('--tag'            , dest='tag'            , help='Tag'                          , default=None)
    parser.add_option('--year'           , dest='year'           , help='Year'                         , default='all')
    parser.add_option('--sigset'         , dest='sigset'         , help='Signal samples'               , default='SM')
    parser.add_option('--reftag'         , dest='reftag'         , help='Tag for input file'           , default=None)
    parser.add_option('--refsigset'      , dest='refsigset'      , help='Sigset for input file'        , default=None)
    parser.add_option('--verbose'        , dest='verbose'        , help='Activate print for debugging' , default=False, action='store_true')
    # read default parsing options as well
    hwwtools.addOptions(parser)
    hwwtools.loadOptDefaults(parser)
    (opt, args) = parser.parse_args()
  
    if 'PseudoDATA' not in opt.sigset:
        print('Error: please include \'Pseudo\' flag in the sigset')
        exit()

    outsigset = opt.sigset
    opt.sigset = '-'.join([ x for x in outsigset.split('-') if 'PseudoDATA' not in x ])
    inputtag = opt.tag
    if opt.reftag==None: opt.reftag = inputtag
    elif opt.reftag!=inputtag:
        for x in outsigset.split('-'):
            if x=='PseudoDATA':
                print('Error: please add a string to \'PseudoDATA\' to charactherize the input tag used to build the data')
                exit()
    if opt.refsigset==None: opt.refsigset = opt.sigset

    opt.outputDirDatacard = 'Dummy'

    for year in opt.year.split():

        if opt.verbose: print('Building', year, 'pseudo-data for', inputtag, opt.sigset, 'from', opt.reftag, opt.refsigset)

        opt.tag = year + inputtag

        dataShapes = {}

        refFile = ROOT.TFile('/'.join([ opt.inputDir, year, opt.reftag, 'plots_'+opt.reftag+'_'+opt.refsigset+'.root' ]), 'read')

        samples = {}
        if os.path.exists(opt.samplesFile) :
            handle = open(opt.samplesFile,'r')
        exec(handle)
        handle.close()

        cuts = {}
        if os.path.exists(opt.cutsFile) :
            handle = open(opt.cutsFile,'r')
            exec(handle)
            handle.close()

        variables = {}
        if os.path.exists(opt.variablesFile) :
            handle = open(opt.variablesFile,'r')
            exec(handle)
            handle.close()

        if opt.verbose: print('      Merging background shapes')        

        for cut in cuts:
            for variable in variables:
                if 'cuts' not in variables[variable] or cut in variables[variable]['cuts']:

                    inputDir = '/'.join([ cut, variable ])
                    if opt.verbose: print('            ', inputDir)

                    for sample in samples:
                        if not samples[sample]['isDATA'] and not samples[sample]['isSignal']:
                            if 'removeFromCuts' not in samples[sample] or cut not in samples[sample]['removeFromCuts']:
        
                                sampleShape = refFile.Get(inputDir+'/histo_'+sample)
                                sampleShape.SetDirectory(0)
                                if inputDir not in dataShapes: dataShapes[inputDir] = sampleShape
                                else: dataShapes[inputDir].Add(sampleShape)

        refFile.Close()

        outputFileName = '/'.join([ opt.inputDir, year, inputtag, 'plots_'+inputtag+'_'+outsigset+'.root' ])
        os.system('cp '+outputFileName.replace(outsigset, opt.sigset)+' '+outputFileName)
        outputFile = ROOT.TFile(outputFileName, 'update')
   
        if opt.verbose: print('      Saving pseudo-data shapes')
 
        for outDir in dataShapes:

            outputFile.cd(outDir)
            outputShape = dataShapes[outDir]
            binContents = []
            for ib in range(1, outputShape.GetNbinsX()+1): binContents.append(outputShape.GetBinContent(ib))
            outputShape.Reset()
            for ib in range(1, outputShape.GetNbinsX()+1):
                binContent = int(round(binContents[ib-1]))
                for ev in range(binContent): outputShape.Fill(outputShape.GetBinCenter(ib))
            outputShape.SetTitle('histo_PseudoDATA')
            outputShape.SetName('histo_PseudoDATA')
            outputShape.Write()

        outputFile.Close()


