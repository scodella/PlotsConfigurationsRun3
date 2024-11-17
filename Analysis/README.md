## Installation of the code

At installation, do this:

    mkdir WorkAreaRDF
    cd WorkAreaRDF

    git clone --branch 13.6TeV https://github.com/scodella/setup LatinosSetup
    ./LatinosSetup/SetupRDFAnalysis.sh [new]RPLME_ANALYSIS [keep][BASE]

    cd mkShapesRDF
    ./install.sh 

    bash
    source start.sh

    cd ../PlotsConfigurationsRun3/Analysis

If already installed, just do:

    cd WorkAreaRDF/mkShapesRDF
    bash
    source start.sh
    cd ../PlotsConfigurationsRun3/Analysis



