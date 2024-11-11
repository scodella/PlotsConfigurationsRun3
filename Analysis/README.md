## Installation of the code

The code used is documented here:

    https://github.com/scodella/setup/blob/13.6TeV/SetupAnalysis.sh

To install, try this

    setenv SCRAM_ARCH el9_amd64_gcc12
    cmsrel CMSSW_X_Y_Z
    cd CMSSW_X_Y_Z/src
    cmsenv
    git clone --branch 13.6TeV https://github.com/scodella/setup LatinosSetup
    ./LatinosSetup/SetupAnalysis.sh RPLME_ANALYSIS

Copy the file LatinoAnalysis/Tools/python/userConfig_TEMPLATE.py to LatinoAnalysis/Tools/python/userConfig.py and edit it to reflect your local paths. This is needed for batch jobs submission.

Compile all from CMSSW_X_Y_Z/src.


