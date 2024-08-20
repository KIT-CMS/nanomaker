#!/bin/bash
CMSSW_VERSION=$1
if [ ! -d "CMSSW_${CMSSW_VERSION}" ]; then
    export VO_CMS_SW_DIR=/cvmfs/cms.cern.ch
    source $VO_CMS_SW_DIR/cmsset_default.sh
    scram project CMSSW_${CMSSW_VERSION}
    cd CMSSW_${CMSSW_VERSION}/src
    eval `scramv1 runtime -sh`
    scramv1 b -j 12
fi