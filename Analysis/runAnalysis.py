#!/usr/bin/env python3
import optparse
import sys
import os
sys.path.append(os.path.abspath('../Tools/python'))
import commonTools
import latinoTools 
import combineTools 
import analysisTools

if __name__ == '__main__':

    # Input parameters
    usage = 'usage: %prog [options]'
    parser = optparse.OptionParser(usage)
    
    parser.add_option('--action'          , dest='action'          , help='Action to be performed'         , default='shapes')
    parser.add_option('--configuration'   , dest='configuration'   , help='Configuration file'             , default='configuration.py')
    parser.add_option('--configsFolder'   , dest='configsFolder'   , help='Directory to store RDF configs' , default='./configs')
    parser.add_option('--tag'             , dest='tag'             , help='Tag'                            , default='test')
    parser.add_option('--year'            , dest='year'            , help='year'                           , default='test')
    parser.add_option('--sigset'          , dest='sigset'          , help='Sample to run on'               , default='SM')
    parser.add_option('--fileset'         , dest='fileset'         , help='Input shape file'               , default='')
    parser.add_option('--option'          , dest='option'          , help='Options for the action'         , default='')
    parser.add_option('--treeName'        , dest='treeName'        , help='Name of the input tree'         , default='Events')
    parser.add_option('--keepallplots'    , dest='keepallplots'    , help='Keep all plots'                 , default=False, action='store_true')
    parser.add_option('--paperStyle'      , dest='paperStyle'      , help='Use paper style'                , default=False, action='store_true')
    parser.add_option('--shapedir'        , dest='shapedir'        , help='Directory to store shapes'      , default='./Shapes')
    parser.add_option('--plotsdir'        , dest='plotsdir'        , help='Directory to store plots'       , default='./Plots')
    parser.add_option('--cardsdir'        , dest='cardsdir'        , help='Directory to store datacards'   , default='./Datacards')
    parser.add_option('--limitdir'        , dest='limitdir'        , help='Directory to store limits'      , default='./Limits')
    parser.add_option('--gofitdir'        , dest='gofitdir'        , help='Directory to store GOF results' , default='./GoodnessOfFits')
    parser.add_option('--mlfitdir'        , dest='mlfitdir'        , help='Directory to store ML fits'     , default='./MaxLikelihoodFits')
    parser.add_option('--impactdir'       , dest='impactdir'       , help='Directory to store impacts'     , default='./Impacts')
    parser.add_option('--tabledir'        , dest='tabledir'        , help='Directory to store tables'      , default='./Tables')
    parser.add_option('--datadir'         , dest='datadir'         , help='Directory to store input data'  , default='./Data')
    parser.add_option('--batchQueue'      , dest='batchQueue'      , help='Queue for the batch jobs'       , default='cms_high')
    parser.add_option('--batchFolder'     , dest='batchFolder'     , help='Directory with log files'       , default='./condor')
    parser.add_option('--logprocess'      , dest='logprocess'      , help='Process for log inspection'     , default='mkShapes')
    parser.add_option('--dryRun'          , dest='dryRun'          , help='do not submit jobs'             , default=False, action='store_true')
    parser.add_option('--interactive'     , dest='interactive'     , help='Run jobs in interactive'        , default=False, action='store_true')
    parser.add_option('--debug'           , dest='debug'           , help='Print command (no execute it)'  , default=False, action='store_true')
    parser.add_option('--unblind'         , dest='unblind'         , help='Unblind data in limits'         , default=False, action='store_true')
    parser.add_option('--verbose'         , dest='verbose'         , help='Activate debug printing'        , default=False, action='store_true')
    parser.add_option('--checkjobs'       , dest='checkjobs'       , help='Check jobs status'              , default=False, action='store_true')
    parser.add_option('--reset'           , dest='reset'           , help='Reset and restart jobs'         , default=False, action='store_true')
    parser.add_option('--recover'         , dest='recover'         , help='Recover failed jobs'            , default=False, action='store_true')
    parser.add_option('--force'           , dest='force'           , help='Enforce action'                 , default=False, action='store_true')
    parser.add_option('--merge'           , dest='merge'           , help='Merge the shapes'               , default=False, action='store_true')
    parser.add_option('--deepMerge'       , dest='deepMerge'       , help='Merge shepes in deep mode'      , default=None)
    parser.add_option('--combineLocation' , dest='combineLocation' , help='Combine CMSSW Directory'        , default='COMBINE')
    parser.add_option('--iihe-wall-time'  , dest='IiheWallTime'    , help='Requested IIHE queue Wall Time' , default='168:00:00')
    (opt, args) = parser.parse_args()

    # Analysis defaults
    analysisTools.setAnalysisDefaults(opt)

    # Run required action
    for tool in [ commonTools, latinoTools, combineTools, analysisTools ]:
        if hasattr(tool, opt.action):
            module = getattr(tool, opt.action)
            module(opt)

