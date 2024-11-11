#!/usr/bin/env python3
import optparse
import json
import os
import ROOT
import copy
import LatinoAnalysis.Gardener.hwwtools as hwwtools

if __name__ == '__main__':

    usage = 'usage: %prog [options]'
    parser = optparse.OptionParser(usage)

    parser.add_option('--inputDir'       , dest='inputDir'       , help='Input directory'                    , default='./Shapes')
    parser.add_option('--tag'            , dest='tag'            , help='Tag used for the shape file name'   , default=None)
    parser.add_option('--years'          , dest='years'          , help='Years'                              , default='all')
    parser.add_option('--sigset'         , dest='sigset'         , help='Signal samples [SM]'                , default='SM')
    parser.add_option('--outputShapeDir' , dest='outputShapeDir' , help='Output directory'                   , default=None)
    parser.add_option('--skipLNN'        , dest='skipLNN'        , help='Skip lnN nuisances'                 , default=False, action='store_true')
    parser.add_option('--saveNuisances'  , dest='saveNuisances'  , help='Save file with merged nuisances'    , default=False, action='store_true')
    parser.add_option('--nuisancesFile'  , dest='nuisancesFile'  , help='File with nuisances configurations' , default=None )
    parser.add_option('--outputNuisFile' , dest='outputNuisFile' , help='File with output nuisances'         , default=None)
    parser.add_option('--verbose'        , dest='verbose'        , help='Activate print for debugging'       , default=False, action='store_true')
    # read default parsing options as well
    hwwtools.addOptions(parser)
    hwwtools.loadOptDefaults(parser)
    (opt, args) = parser.parse_args()

    years = opt.years.split('-')

    if len(years)==1:
        print('mergeDataTakingPeriodShapes: nothing to do with one year')
        exit()

    outputNuisancesFile = opt.outputNuisFile if opt.outputNuisFile!=None else opt.nuisancesFile.replace('.py', '_'.join([opt.years, opt.tag, opt.sigset])+'.py')

    allnuisances = {}

    tag = opt.tag

    for period in years:

        opt.tag = period + tag

        samples = {}
        if os.path.exists(opt.samplesFile) :
            handle = open(opt.samplesFile,'r')
            exec(handle.read())
            handle.close()

        cuts = {}
        if os.path.exists(opt.cutsFile) :
            handle = open(opt.cutsFile,'r')
            exec(handle.read())
            handle.close()

        variables = {}
        if os.path.exists(opt.variablesFile) :
            handle = open(opt.variablesFile,'r')
            exec(handle.read())
            handle.close()

        nuisances = {}
        if os.path.exists(opt.nuisancesFile) :
            handle = open(opt.nuisancesFile,'r')
            exec(handle.read())
            handle.close()

        for nuisance in nuisances:
            if opt.skipLNN and 'type' in nuisances[nuisance] and nuisances[nuisance]['type']=='lnN': continue
            if nuisance!='stat': 
                nuisanceKey = nuisance+'__'+nuisances[nuisance]['name']
                if nuisanceKey not in allnuisances:
                    allnuisances[nuisanceKey] = nuisances[nuisance].copy()
                else:
                    for sample in nuisances[nuisance]['samples']:
                        if sample not in allnuisances[nuisanceKey]['samples']:
                            allnuisances[nuisanceKey]['samples'][sample] = nuisances[nuisance]['samples'][sample]
                if 'type' in nuisances[nuisance] and nuisances[nuisance]['type']=='lnN':
                    allnuisances[nuisanceKey]['samples_'+period] = nuisances[nuisance]['samples']
            elif 'stat' not in allnuisances:
                allnuisances['stat'] = nuisances[nuisance]

    outDirName = opt.outputShapeDir if opt.outputShapeDir!=None else '/'.join([ opt.inputDir, opt.years, tag ])
    os.system ('mkdir -p ' + outDirName)

    outFileName = '/plots_' + tag + '_' + opt.sigset + '.root'
    outFile = ROOT.TFile.Open(outDirName+outFileName, 'recreate') 

    inFiles = [ ]
    for year in years:
        if not os.path.isfile('/'.join([ opt.inputDir, year, tag ])+outFileName): 
            print('Error in mergeDataTakingPeriodShapes: input file', '/'.join([ opt.inputDir, year, tag ])+outFileName, 'not found') 
            exit()
        inFiles.append([ ROOT.TFile('/'.join([ opt.inputDir, year, tag ])+outFileName, 'READ') , year ])

    missingSampleList = [ ]
       
    for cutName in cuts:

        outFile.mkdir(cutName)
        for variableName in variables:
            if 'cuts' not in variables[variableName] or cutName in variables[variableName]['cuts']:

                folderName = cutName + '/' + variableName
                outFile.mkdir(folderName)

                if opt.verbose: print('################################', folderName)

                inDirs = [ ] 
                for infile in inFiles:
                    inDirs.append([ infile[0].Get(folderName), infile[1] ])

                for sample in samples:
                                   
                    for nuisance in allnuisances:
                        if (sample in allnuisances[nuisance]['samples'] or nuisance=='stat') and ('cuts' not in allnuisances[nuisance] or cutName in allnuisances[nuisance]['cuts']):   

                            if nuisance!='stat': 
                                if 'type' not in allnuisances[nuisance]:
                                    print('Warning: nuisance without type -> ', nuisance)
                                    continue
                                if allnuisances[nuisance]['type']!='shape' and allnuisances[nuisance]['type']!='lnN':
                                    if allnuisances[nuisance]['type']!='rateParam':
                                        print('Warning: unknown nuisance type -> ', allnuisances[nuisance]['type'])
                                    continue

                            shapeName = 'histo_' + sample

                            for var in [ 'Up', 'Down' ]:

                                if nuisance=='stat' and var=='Down': continue 
                                 
                                shapeVar = shapeName if nuisance=='stat' else shapeName + '_' + allnuisances[nuisance]['name'] + var
                                  
                                for idir, indir in enumerate(inDirs):

                                    if indir[0].GetListOfKeys().Contains(shapeVar):
                                        tmpHisto = indir[0].Get(shapeVar)
                                        tmpHisto.SetDirectory(0)   

                                    elif indir[0].GetListOfKeys().Contains(shapeName):
                                        tmpHisto = indir[0].Get(shapeName)
                                        tmpHisto.SetDirectory(0)

                                        if allnuisances[nuisance]['type']=='lnN':
                                            if 'samples_'+indir[1] in allnuisances[nuisance]:
                                                if sample in allnuisances[nuisance]['samples_'+indir[1]]:
                                                    systNorm = float(allnuisances[nuisance]['samples_'+indir[1]][sample])
                                                    if var=='Down': systNorm = 2. - systNorm
                                                    tmpHisto.Scale(systNorm)
                                                    if opt.verbose: print('samples_'+indir[1], tmpHisto.Integral())
                                            elif indir[1] in nuisance:
                                                print('Error: samples_'+indir[1]+' not in allnuisances['+nuisance+']')

                                    else:
                                        if indir[1]+'_'+sample not in missingSampleList:
                                            print('Warning:', sample, 'not in input shape file for', cutName, 'in', indir[1], 'year!')
                                            missingSampleList.append(indir[1]+'_'+sample)
                                        for idir2, indir2 in enumerate(inDirs):
                                            if indir2[0].GetListOfKeys().Contains(shapeName):
                                                tmpHisto = indir2[0].Get(shapeName)
                                                tmpHisto.SetDirectory(0)
                                                tmpHisto.Reset()

                                    if opt.verbose: print(indir[1], sample, nuisance,  var, tmpHisto.Integral())

                                    if idir==0:
                                        sumHisto = tmpHisto.Clone()
                                        sumHisto.SetDirectory(0)
                                        sumHisto.SetTitle(shapeVar)
                                        sumHisto.SetName(shapeVar)
                                    else:
                                        sumHisto.Add(tmpHisto)

                                outFile.cd(folderName)
                                sumHisto.Write()                         

                                # ...    
 
    if opt.saveNuisances:     
        with open(outputNuisancesFile,'w') as file:
            for nuisance in allnuisances:
                if allnuisances[nuisance]['type']=='lnN':
                    allnuisances[nuisance]['type'] = 'shape'
                    allnuisances[nuisance]['waslnN'] = True
                #file.write('nuisances[\''+nuisance+'\'] = '+json.dumps(allnuisances[nuisance])+'\n\n')
                file.write('nuisances[\''+nuisance+'\'] = '+repr(allnuisances[nuisance])+'\n\n')

    if opt.verbose: print("Output file:", outDirName+outFileName)
    
