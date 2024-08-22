import os
import luigi
from framework import console
from framework import Task
import tarfile
import shutil
from helpers.helpers import create_abspath


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
            f"{self.cmssw_version}_{self.production_tag}.tar.gz"
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
        run_script_path = os.path.join(install_dir, cmssw_version, "src")
        create_abspath(install_dir)
        setup_script = os.path.join(
            str(os.path.abspath("processor")), "tasks", "scripts", "setup_cmssw.sh"
        )
        tarball = os.path.join(os.path.abspath(install_dir), output.basename)
        # setup cmssw, compile, generate cmsrun config and build the tarball
        if not self.cmsrun_script:
            run_cmsDriver = True
            cmsdriver_command = f"'{self.cmsdriver_command}'"
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
        self.run_command_readable(command, run_location=install_dir)
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
            self.run_command_readable(command, run_location=run_script_path)
        else:
            # copy the cmsrun script to the install dir
            shutil.copy(self.cmsrun_script, run_script_path)
        # add some additional lines to the end of cms_run_config
        additional_lines_file = os.path.join(
            str(os.path.abspath("processor")),
            "tasks",
            "scripts",
            "cmssw_additional_lines.txt",
        )
        with open(additional_lines_file, "r") as f:
            additional_lines = f.read()
        with open(os.path.join(run_script_path, cms_run_config), "a") as f:
            f.write(additional_lines)
        # create tarball with compiled CMSSW folder and the cmsrun config
        with tarfile.open(tarball, "w:gz") as tar:
            tar.add(install_dir, arcname=".")
        # upload an small file to signal that the build is done
        console.log(f"Uploading local tarball {tarball} to {output.uri()}")
        output.copy_from_local(tarball)
        console.rule("Finished CMSSW setup")
