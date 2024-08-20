#!/bin/bash
CMSSW_VERSION=$1
CMSDRIVER_COMMAND="$2"
THREADS=$3
export VO_CMS_SW_DIR=/cvmfs/cms.cern.ch
source $VO_CMS_SW_DIR/cmsset_default.sh
echo "Running cmsDriver in $(pwd)"
eval `scramv1 runtime -sh`
# if there is --nThreads #int replace it with --nThreads $THREADS
if [[ $CMSDRIVER_COMMAND == *"--nThreads"* ]]; then
    CMSDRIVER_COMMAND=$(echo $CMSDRIVER_COMMAND | sed "s/--nThreads [0-9]*/--nThreads $THREADS/")
else
    CMSDRIVER_COMMAND+=" --nThreads $THREADS"
fi
# if there is --python_filename=some_file.py replace it with --python_filename=nano_config.py
if [[ $CMSDRIVER_COMMAND == *"--python_filename"* ]]; then
    CMSDRIVER_COMMAND=$(echo $CMSDRIVER_COMMAND | sed "s/--python_filename=[a-zA-Z0-9_]*.py/--python_filename=nano_config.py/")
fi
# if there is --fileout file:somefilename.root replace it with --fileout file:nanoAOD.root
if [[ $CMSDRIVER_COMMAND == *"--fileout"* ]]; then
    CMSDRIVER_COMMAND=$(echo $CMSDRIVER_COMMAND | sed "s/--fileout file:[a-zA-Z0-9_]*.root/--fileout file:nanoAOD.root/")
fi
eval $CMSDRIVER_COMMAND