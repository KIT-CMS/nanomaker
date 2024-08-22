# NanoMaker

NanoMaker is a law-based workflow that can be used to generate NanoAOD files from MiniAOD files.

## Installation

First clone the repository:

```bash
git clone --recursive git@github.com:harrypuuter/nanomaker.git
```

Then run the initialization script:

```bash
cd nanomaker
source init.sh
```

## Configuration

Before running a new production of NanoAODs, you have to setup several parameters in the config files and provide a yaml file with the list of samples to process.

### Config files

The relevant configuration parameters are:

#### Output directory

The location, where the NanoAOD files will be stored. By default, all outputs are written to the GridKA NRG storage under `root://cmsdcache-kit-disk.gridka.de//store/user/${USER}/nanomaker/`. If you want to use a different location, change the

```
[wlcg_fs]
base: root://cmsdcache-kit-disk.gridka.de//store/user/${USER}/nanomaker/
use_cache: True
cache_root: /tmp/${USER}/
cache_max_size: 20000
```

part in the `NanoMaker_law.cfg` file, and

```
wlcg_path = root://cmsdcache-kit-disk.gridka.de//store/user/${USER}/nanomaker/
```

in the `NanoMaker_luigi.cfg` file.

#### CMSSW version

The CMSSW version to be used for the production. This can be set in the `NanoMaker_luigi.cfg` file:

```
cmssw_version = CMSSW_13_0_10
```

#### CMS driver command

change this parameter to provide your own cmsdriver command.

```
cmsdriver_command = cmsDriver.py nano --fileout file:nano.root --eventcontent NANOAODSIM --datatier NANOAODSIM --step NANO --nThreads 2 --mc --conditions auto:phase1_2018_realistic --era Run2_2018,run2_nanoAOD_106Xv2 -n 100 --filein inputfile.root --no_exec --python_filename=nano_config.py
```

#### Job parameters

Several parameters are used to control the job parameters of the HTCondor jobs, including

```
htcondor_accounting_group = cms.production
htcondor_remote_job = True
htcondor_request_cpus = 4
htcondor_universe = docker
files_per_task = 5

[..]

[RunCMSSW]
htcondor_walltime = 10800
htcondor_request_memory = 16000
htcondor_requirements = TARGET.ProvidesCPU && TARGET.ProvidesIO
htcondor_request_disk = 20000000
```

Change these parameters to your needs.

### Sample list

The samples to be processed are provided as a yaml file with the following structure:

```yaml
"2018": # era
  "dy": # sampletype
    YourChosenNickForTheSample: /CMS/DAS/Name
    # DYJetsToLL_M-10to50-madgraphMLM: /DYJetsToLL_M-10to50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIISummer20UL18MiniAODv2-106X_upgrade2018_realistic_v16_L1v1-v1/MINIAODSIM
"2017":
  "ttbar":
    YourChosenNickForTheSample: /CMS/DAS/Name
[...]
```

The era, sampletype and nicknames are used to create the output directory structure. The output structure will be

```
root://cmsdcache-kit-disk.gridka.de//store/user/${USER}/nanomaker/${production_tag}/RunCMSSW/{era}/${nickname}/${nickname}_*.root
```

where `${production_tag}` is the tag of the production, `${era}` is the era of the sample, `${nickname}` is the nickname of the sample and `*` is the job number.


## Usage

The main command to run NanoMaker is:

```bash
law run ProduceNanoAOD --sampledict path/to/your/sampledict/yaml --production-tag your_production_tag
```