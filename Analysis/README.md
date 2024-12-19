## Installation of the code

At installation, do this:

    mkdir BTagPerfRDF
    cd BTagPerfRDF

    git clone --branch 13.6TeV https://github.com/scodella/setup LatinosSetup
    ./LatinosSetup/SetupRDFAnalysis.sh BTagPerf

    cd mkShapesRDF
    ./install.sh 

    bash
    source start.sh

    cd ../PlotsConfigurationsRun3/Analysis

If already installed, just do:

    cd BTagPerfRDF/mkShapesRDF
    bash
    source start.sh
    cd ../PlotsConfigurationsRun3/Analysis

## Production of weights for kinematic reweighting

The scripts to derive the scale factors are in PlotsConfigurationsRun3/BTagPerf.
The first step is the production of the raw histograms (aka shapes) for the kinematic variables:

    ../runAnalysis.py --action=shapes --year=CAMPAIGNNAME --tag=System8Kinematics/PtRelKinematics

Job status can be check by:

    ../runAnalysis.py --action=shapes --year=CAMPAIGNNAME --tag=System8Kinematics/PtRelKinematics --checkjobs

Failed jobs can be resubmitted by:

    ../runAnalysis.py --action=shapes --year=CAMPAIGNNAME --tag=System8Kinematics/PtRelKinematics --recover

When all jobs are done, shapes can be merged by

    ../runAnalysis.py --action=shapes --year=CAMPAIGNNAME --tag=System8Kinematics/PtRelKinematics --merge --sigset=MC
    ../runAnalysis.py --action=shapes --year=CAMPAIGNNAME --tag=System8Kinematics/PtRelKinematics --merge --sigset=Data

Then weights as a function of the jet pt can be derived:

    ../runAnalysis.py --action=kinematicWeights --year=CAMPAIGNNAME --tag=System8Kinematics/PtRelKinematics --option=mujetpt

Now, we can produce the shapes with the weights applied ...

    ../runAnalysis.py --action=shapes --year=CAMPAIGNNAME --tag=System8Kinematics.mujetpt/PtRelKinematics.mujetpt --sigset=MC
    ../runAnalysis.py --action=mergesingle --year=CAMPAIGNNAME --tag=System8Kinematics.mujetpt/PtRelKinematics.mujetpt --sigset=MC

... and make some validation plot:

    ../runAnalysis.py --action=plotKinematics --year=CAMPAIGNNAME --tag=System8Kinematics.mujetpt/PtRelKinematics.mujetpt

Finally, we can compute weights as a function of the jet eta on top of the one as a function of the jet pt, but using a finer pt binning (ProdRun2) ...

    ../runAnalysis.py --action=shapes --year=CAMPAIGNNAME --tag=System8KinematicsProdRun2.mujetpt/PtRelKinematicsProdRun2.mujetpt --sigset=MC
    ../runAnalysis.py --action=shapes --year=CAMPAIGNNAME --tag=System8KinematicsProdRun2.mujetpt/PtRelKinematicsProdRun2.mujetpt --sigset=MC --merge
    ../runAnalysis.py --action=shapes --year=CAMPAIGNNAME --tag=System8KinematicsProdRun2/PtRelKinematicsProdRun2 --sigset=Data 
    ../runAnalysis.py --action=shapes --year=CAMPAIGNNAME --tag=System8KinematicsProdRun2/PtRelKinematicsProdRun2 --sigset=Data --merge
    ../runAnalysis.py --action=kinematicWeights --year=CAMPAIGNNAME --tag=System8KinematicsProdRun2.mujetpt/PtRelKinematicsProdRun2.mujetpt --option=mujeteta

... and try their effect:

    ../runAnalysis.py --action=shapes --year=CAMPAIGNNAME --tag=System8KinematicsProdRun2.mujetpt.mujeteta/PtRelKinematicsProdRun2.mujetpt.mujeteta --sigset=MC
    ../runAnalysis.py --action=shapes --year=CAMPAIGNNAME --tag=System8KinematicsProdRun2.mujetpt.mujeteta/PtRelKinematicsProdRun2.mujetpt.mujeteta --sigset=MC --merge
    ../runAnalysis.py --action=plotKinematics --year=CAMPAIGNNAME --tag=System8KinematicsProdRun2.mujetpt.mujeteta/PtRelKinematicsProdRun2.mujetpt.mujeteta

## Production of templates for PtRel/System8 fits

First step is the production of the shapes for the System8/PtRel fits:

    ../runAnalysis.py --action=makeShapes --year=CAMPAIGNNAME --tag=System8Templates.mujetpt.mujeteta/PtRelTemplates.mujetpt.mujeteta

Shapes can be merged by

    ../runAnalysis.py --action=mergeShapes --year=CAMPAIGNNAME --tag=System8Templates.mujetpt.mujeteta/PtRelTemplates.mujetpt.mujeteta

If some shapes were missing, they can be recovered by doing:

    ../runAnalysis.py --action=recoverShapes --year=CAMPAIGNNAME --tag=System8Templates.mujetpt.mujeteta/PtRelTemplatesMuPtDown.mujetpt.mujeteta

Finally, the format of the shapes need to be converted to the input format for the System8/PtRel fits:

    ../runAnalysis.py --action=shapesForFit --year=CAMPAIGNNAME --tag=System8Templates.mujetpt.mujeteta/PtRelTemplates.mujetpt.mujeteta # To be complete

## Fits and scale factors


