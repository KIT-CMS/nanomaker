import os
import luigi
from framework import console
from framework import Task
import tarfile
import shutil


class SetupCMSSW(Task):
    """
    Gather and compile CROWN with the given configuration
    """

    install_dir = luigi.Parameter()
    cmssw_version = luigi.Parameter()
    cmsdriver_command = luigi.Parameter()
    cmsrun_script = luigi.Parameter(significant=False, default="")
    htcondor_request_cpus = luigi.IntParameter(default=1)
    production_tag = luigi.Parameter()

    def output(self):
        # sort the sample types and eras to have a unique string for the tarball
        target = self.remote_target(
            f"cmssw_{self.cmssw_version}_{self.production_tag}.tar.gz"
        )
        return target

    def run(self):
        # get output file path
        output = self.output()
        cmssw_version = self.cmssw_version
        threads = str(self.htcondor_request_cpus)
        # also use the tag for the local tarball creation
        tag = self.production_tag
        install_dir = os.path.join(str(self.install_dir), tag)
        setup_script = os.path.join(
            str(os.path.abspath("processor")), "tasks", "scripts", "setup_cmssw.sh"
        )
        tarball = os.path.join(install_dir, output.basename)
        # setup cmssw, compile, generate cmsrun config and build the tarball
        if not self.cmsrun_script:
            run_cmsDriver = True
            cmsdriver_command = self.cmsdriver_command
            cms_run_config = "nano_config.py"
        else:
            run_cmsDriver = False
            cmsdriver_command = None
            cms_run_config = self.cmsrun_script
        # actual payload:
        console.rule(f"Setting up CMSSW {cmssw_version}")
        console.rule(f"Installdir: {install_dir}")
        console.rule("")

        # run crown compilation script to setup and compile cmssw
        command = [
            "bash",
            setup_script,
            cmssw_version,  # cmssw_version=$1
        ]
        self.run_command_readable(command)
        # generate the cmsrun config
        if run_cmsDriver:
            cms_run_script = os.path.join(
                str(os.path.abspath("processor")),
                "tasks",
                "scripts",
                "run_cmssw_command.sh",
            )
            command = [
                "bash",
                cms_run_script,
                cmssw_version,  # cmssw_version=$1
                cmsdriver_command,  # cmsdriver_command=$2
                threads,  # threads=$3
            ]
            self.run_command_readable(command)
        else:
            # copy the cmsrun script to the install dir
            shutil.copy(self.cmsrun_script, install_dir)
        # add some additional lines to the end of cms_run_config
        additional_lines = """
            import FWCore.ParameterSet.VarParsing as VarParsing

            options = VarParsing.VarParsing("analysis")
            options.inputFiles = "inputfile_1.root", "inputfile_2.root"
            options.maxEvents = -1
            options.parseArguments()

            process.source = cms.Source(
                "PoolSource",
                fileNames=cms.untracked.vstring(options.inputFiles),
                secondaryFileNames=cms.untracked.vstring(),
            )

            process.maxEvents = cms.untracked.PSet(input=cms.untracked.int32(options.maxEvents))
            """
        with open(os.path.join(install_dir, cms_run_config), "a") as f:
            f.write(additional_lines)
        # create tarball with compiled CMSSW folder and the cmsrun config
        with tarfile.open(tarball, "w:gz") as tar:
            tar.add(os.path.join(install_dir, f"CMSSW_{cmssw_version}"))
            tar.add(os.path.join(install_dir, cms_run_config))
            tar.add(
                os.path.join(
                    str(os.path.abspath("processor")),
                    "tasks",
                    "scripts",
                    "source_cmssw.sh",
                )
            )
        console.rule("Finished CMSSW setup")
        # upload an small file to signal that the build is done
        output.copy_from_local(tarball)
