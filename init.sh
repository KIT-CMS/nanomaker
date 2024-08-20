#!/bin/bash
export PARSED_ENVS="kingmaker"
# Ensure that submodule with KingMaker env files is present
if [ -z "$(ls -A kingmaker-images)" ]; then
    git submodule update --init --recursive -- kingmaker-images
fi
# Get kingmaker-images submodule hash to find the correct image during job submission
export IMAGE_HASH=$(cd kingmaker-images/; git rev-parse --short HEAD)
# setup miniforge
# First listed is env of DEFAULT and will be used as the starting env
# Remaining envs should be sourced via provided docker images
export STARTING_ENV=$(echo ${PARSED_ENVS} | head -n1 | awk '{print $1;}')
# echo "The following envs will be set up: ${PARSED_ENVS}"
echo "${STARTING_ENV}_${IMAGE_HASH} will be sourced as the starting env."
# Check if necessary environment is present in cvmfs
# Try to install and export env via miniforge if not
# NOTE: miniforge is based on conda and uses the same syntax. Switched due to licensing concerns.
# NOTE2: HTCondor jobs that rely on exported miniforge envs might need additional scratch space
if [[ -d "/cvmfs/etp.kit.edu/LAW_envs/miniforge/envs/${STARTING_ENV}_${IMAGE_HASH}" ]]; then
    echo "${STARTING_ENV}_${IMAGE_HASH} environment found in cvmfs."
    echo "Activating starting-env ${STARTING_ENV}_${IMAGE_HASH} from cvmfs."
    source /cvmfs/etp.kit.edu/LAW_envs/miniforge/bin/activate ${STARTING_ENV}_${IMAGE_HASH}
else
    if [ ! -f "miniforge/bin/activate" ]; then
        # Miniforge version used for all environments
        MAMBAFORGE_VERSION="24.3.0-0"
        MAMBAFORGE_INSTALLER="Mambaforge-${MAMBAFORGE_VERSION}-$(uname)-$(uname -m).sh"
        echo "Miniforge could not be found, installing miniforge version ${MAMBAFORGE_INSTALLER}"
        echo "More information can be found in"
        echo "https://github.com/conda-forge/miniforge"
        curl -L -O https://github.com/conda-forge/miniforge/releases/download/${MAMBAFORGE_VERSION}/${MAMBAFORGE_INSTALLER}
        bash ${MAMBAFORGE_INSTALLER} -b -s -p miniforge
        rm -f ${MAMBAFORGE_INSTALLER}
    fi
    # Source base env of miniforge
    source miniforge/bin/activate ''
    # Check if correct miniforge env is running
    if [ -d "miniforge/envs/${STARTING_ENV}_${IMAGE_HASH}" ]; then
        echo  "${STARTING_ENV}_${IMAGE_HASH} env found using miniforge."
    else
        # Create miniforge env from yaml file if necessary
        echo "Creating ${STARTING_ENV}_${IMAGE_HASH} env from kingmaker-images/KingMaker_envs/${STARTING_ENV}_env.yml..."
        if [[ ! -f "kingmaker-images/KingMaker_envs/${STARTING_ENV}_env.yml" ]]; then
            echo "kingmaker-images/KingMaker_envs/${STARTING_ENV}_env.yml not found. Unable to create environment."
            return 1
        fi
        conda env create -f kingmaker-images/KingMaker_envs/${STARTING_ENV}_env.yml -n ${STARTING_ENV}_${IMAGE_HASH}
        echo  "${STARTING_ENV}_${IMAGE_HASH} env built using miniforge."
    fi
    echo "Activating starting-env ${STARTING_ENV}_${IMAGE_HASH} from miniforge."
    conda activate ${STARTING_ENV}_${IMAGE_HASH}
fi
