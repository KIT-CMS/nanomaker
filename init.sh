#!/bin/bash
export ENVNAME="nanomaker"
# setup miniforge
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
# check if env exists, if not create it
if [ -d "miniforge/envs/${ENVNAME}" ]; then
    echo "${ENVNAME} env found using miniforge."
else
    # Create miniforge env from yaml file if necessary
    echo "Creating ${ENVNAME} env ${ENVNAME}_env.yml..."
    if [[ ! -f "${ENVNAME}_env.yml" ]]; then
        echo "${ENVNAME}_env.yml not found. Unable to create environment."
        return 1
    fi
    conda env create -f ${ENVNAME}_env.yml -n ${ENVNAME}
    echo "${ENVNAME} env built using miniforge."
fi
echo "Activating starting-env ${ENVNAME} from miniforge."
conda activate ${ENVNAME}
