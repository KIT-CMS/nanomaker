export VO_CMS_SW_DIR=/cvmfs/cms.cern.ch
source $VO_CMS_SW_DIR/cmsset_default.sh
# check if there is a folder called CMSSW_some_version if yes, go to src
# Define the pattern for the folder name
folder_pattern="CMSSW_*"
# Find the folder matching the pattern
folder=$(find . -maxdepth 1 -type d -name "$folder_pattern" | head -n 1)
# Check if the folder exists
if [ -d "$folder" ]; then
    # Change into the src directory within the folder
    cd "$folder/src"
    eval $(scramv1 runtime -sh)
else
    echo "CMSSW folder not found. Exiting."
    exit 1
fi
