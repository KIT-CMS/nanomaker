############################################################################################
#         This script sets up all dependencies necessary for running NanoMaker             #
############################################################################################


_addpy() {
    [ ! -z "$1" ] && export PYTHONPATH="$1:${PYTHONPATH}"
}

_addbin() {
    [ ! -z "$1" ] && export PATH="$1:${PATH}"
}

action() {
    export PARSED_ENVS="KingMaker"
    export ANA_NAME="NanoMaker"
    local BASE_DIR="$( cd "$( dirname "${THIS_FILE}" )" && pwd )" # Get the directory of this file
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
    # Check is law was set up, and do so if not
        if [ -z "$(ls -A law)" ]; then
            git submodule update --init --recursive -- law
        fi
    # Check for voms proxy
    voms-proxy-info -exists &>/dev/null
    if [[ "$?" -eq "1" ]]; then
        echo "No valid voms proxy found, remote storage might be inaccessible."
        echo "Please ensure that it exists and that 'X509_USER_PROXY' is properly set."
    fi
    # First check if the user already has a luigid scheduler running
    # Start a luidigd scheduler if there is one already running
    if [ -z "$(pgrep -u ${USER} -f luigid)" ]; then
        echo "Starting Luigi scheduler... using a random port"
        while
            export LUIGIPORT=$(shuf -n 1 -i 49152-65535)
            netstat -atun | grep -q "$LUIGIPORT"
        do
            continue
        done
        luigid --background --logdir logs --state-path luigid_state.pickle --port=$LUIGIPORT
        echo "Luigi scheduler started on port $LUIGIPORT, setting LUIGIPORT to $LUIGIPORT"
    else
        # first get the (first) PID
        export LUIGIPID=$(pgrep -u ${USER} -f luigid | head -n 1)
        # now get the luigid port that the scheduler is using and set the LUIGIPORT variable
        export LUIGIPORT=$(cat /proc/${LUIGIPID}/cmdline | sed -e "s/\x00/ /g" | cut -d "=" -f2)
        echo "Luigi scheduler already running on port ${LUIGIPORT}, setting LUIGIPORT to ${LUIGIPORT}"
    fi

    echo "Setting up Luigi/Law ..."
    export LAW_HOME="${BASE_DIR}/.law/${ANA_NAME}"
    export LAW_CONFIG_FILE="${BASE_DIR}/lawluigi_configs/${ANA_NAME}_law.cfg"
    export LUIGI_CONFIG_PATH="${BASE_DIR}/lawluigi_configs/${ANA_NAME}_luigi.cfg"
    export ANALYSIS_PATH="${BASE_DIR}"
    export ANALYSIS_DATA_PATH="${ANALYSIS_PATH}/data"

    # law
    _addpy "${BASE_DIR}/law"
    _addbin "${BASE_DIR}/law/bin"
    source "$( law completion )"
    if [[ "$?" -eq "1" ]]; then
        echo "Law completion failed."
        return 1
    fi

    # tasks
    _addpy "${BASE_DIR}/processor"
    _addpy "${BASE_DIR}/processor/tasks"

    # Create law index for workflow if not previously done
    if [[ ! -f "${LAW_HOME}/index" ]]; then
        law index --verbose
        if [[ "$?" -eq "1" ]]; then
            echo "Law index failed."
            return 1
        fi
    fi
    function monitor_production () {
        # Parse all user arguments and pass them to the python script
        python3 scripts/ProductionStatus.py $@
    }
}
action "$@"