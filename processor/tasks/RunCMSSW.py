import law
import luigi
import os
from SetupCMSSW import SetupCMSSW
import tarfile
from ConfigureDatasets import ConfigureDatasets
import subprocess
from framework import console
from law.config import Config
from framework import HTCondorWorkflow
from helpers.helpers import create_abspath


class RunCMSSW(HTCondorWorkflow, law.LocalWorkflow):
    """
    Gather and compile CROWN with the given configuration
    """

    output_collection_cls = law.NestedSiblingFileCollection
    nick = luigi.Parameter()
    dasname = luigi.Parameter()
    sample_type = luigi.Parameter()
    era = luigi.Parameter()
    production_tag = luigi.Parameter()
    files_per_task = luigi.IntParameter()
    cmssw_version = luigi.Parameter()

    def htcondor_output_directory(self):
        """
        The function `htcondor_output_directory` returns a WLCGDirectoryTarget object that represents a
        directory in the WLCG file system.
        :return: The code is returning a `law.wlcg.WLCGDirectoryTarget` object.
        """
        # Add identification-str to prevent interference between different tasks of the same class
        # Expand path to account for use of env variables (like $USER)
        if self.is_local_output:
            return law.LocalDirectoryTarget(
                self.local_path(f"htcondor_files/{self.nick}"),
                fs=law.LocalFileSystem(
                    None,
                    base=f"{os.path.expandvars(self.local_output_path)}",
                ),
            )

        return law.wlcg.WLCGDirectoryTarget(
            self.remote_path(f"htcondor_files/{self.nick}"),
            fs=law.wlcg.WLCGFileSystem(
                None,
                base=f"{os.path.expandvars(self.wlcg_path)}",
            ),
        )

    def htcondor_create_job_file_factory(self):
        """
        The function `htcondor_create_job_file_factory` creates a job file factory for HTCondor workflows.
        :return: The method is returning the factory object that is created by calling the
        `htcondor_create_job_file_factory` method of the superclass `HTCondorWorkflow`.
        """
        class_name = self.__class__.__name__
        task_name = [class_name + self.nick]
        _cfg = Config.instance()
        job_file_dir = _cfg.get_expanded("job", "job_file_dir")
        job_files = os.path.join(
            job_file_dir,
            self.production_tag,
            "_".join(task_name),
            "files",
        )
        factory = super(HTCondorWorkflow, self).htcondor_create_job_file_factory(
            dir=job_files,
            mkdtemp=False,
        )
        return factory

    def htcondor_job_config(self, config, job_num, branches):
        class_name = self.__class__.__name__
        condor_batch_name_pattern = f"NanoAOD-{self.nick}-{self.production_tag}"
        config = super().htcondor_job_config(config, job_num, branches)
        config.custom_content.append(("JobBatchName", condor_batch_name_pattern))
        for type in ["log", "stdout", "stderr"]:
            logfilepath = getattr(config, type)
            # split the filename, and add the sample nick as an additional folder
            logfolder, logfile = os.path.split(logfilepath)
            logfolder = os.path.join(logfolder, self.nick)
            # create the new path
            os.makedirs(logfolder, exist_ok=True)
            setattr(config, type, os.path.join(logfolder, logfile))
        return config

    def modify_polling_status_line(self, status_line):
        """
        The function `modify_polling_status_line` modifies the status line that is printed during polling by
        appending additional information based on the class name.

        :param status_line: The `status_line` parameter is a string that represents the current status line
        during polling
        :return: The modified status line with additional information about the class name, analysis,
        configuration, and production tag.
        """
        class_name = self.__class__.__name__
        status_line_pattern = f"{self.nick} (Tag: {self.production_tag})"
        return f"{status_line} - {law.util.colored(status_line_pattern, color='light_cyan')}"

    def workflow_requires(self):
        requirements = {}
        requirements["tarball"] = SetupCMSSW.req(
            self,
            install_dir=self.install_dir,
            cmssw_version=self.cmssw_version,
            cmsrun_command=self.cmsrun_command,
            production_tag=self.production_tag,
            htcondor_request_cpus=self.htcondor_request_cpus,
        )
        requirements["dataset"] = ConfigureDatasets.req(
            self,
            nick=self.nick,
            dasname=self.dasname,
            production_tag=self.production_tag,
            era=self.era,
            sample_type=self.sample_type,
        )

        return requirements

    def requires(self):
        requirements = {}
        requirements["tarball"] = SetupCMSSW.req(
            self,
            install_dir=self.install_dir,
            cmssw_version=self.cmssw_version,
            cmsrun_command=self.cmsrun_command,
            production_tag=self.production_tag,
            htcondor_request_cpus=self.htcondor_request_cpus,
        )
        return requirements

    def create_branch_map(self):
        branch_map = {}
        branchcounter = 0
        dataset = ConfigureDatasets(
            nick=self.nick,
            production_tag=self.production_tag,
            era=self.era,
            sample_type=self.sample_type,
        )
        # since we use the filelist from the dataset, we need to run it first
        dataset.run()
        datsetinfo = dataset.output()
        with datsetinfo.localize("r") as _file:
            inputdata = _file.load()
        branches = {}
        if len(inputdata["filelist"]) == 0:
            raise Exception("No files found for dataset {}".format(self.nick))
        files_per_task = self.files_per_task
        for filecounter, filename in enumerate(inputdata["filelist"]):
            if (int(filecounter / files_per_task)) not in branches:
                branches[int(filecounter / files_per_task)] = []
            branches[int(filecounter / files_per_task)].append(filename)
        for x in branches:
            branch_map[branchcounter] = {}
            branch_map[branchcounter]["nick"] = self.nick
            branch_map[branchcounter]["era"] = self.era
            branch_map[branchcounter]["sample_type"] = self.sample_type
            branch_map[branchcounter]["files"] = branches[x]
            branchcounter += 1
        return branch_map

    def output(self):
        targets = []
        nicks = [
            "{era}/{nick}/{nick}_{branch}.root".format(
                era=self.branch_data["era"],
                nick=self.branch_data["nick"],
                branch=self.branch,
            )
        ]
        targets = self.remote_target(nicks)
        for target in targets:
            target.parent.touch()
        return targets

    def run(self):
        outputs = self.output()
        outputfile = outputs[0]
        branch_data = self.branch_data
        base_workdir = os.path.abspath("workdir")
        create_abspath(base_workdir)
        workdir = os.path.join(base_workdir, f"{self.production_tag}")
        create_abspath(workdir)
        inputfiles = branch_data["files"]
        tarball = self.input()["tarball"]
        console.log(f"Getting CMSSW tarball from {tarball.uri()}")
        with tarball.localize("r") as _file:
            tarballpath = _file.path
        # first unpack the tarball if the exec is not there yet
        tar = tarfile.open(tarballpath, "r:gz")
        tar.extractall(workdir)
        # test running the source command
        console.rule("Source CMSSW environment")
        # set environment using env script
        my_env = self.set_environment(f"{workdir}/source_cmssw.sh {self.cmssw_version}")
        input_files = [f"inputFiles={x}" for x in inputfiles]
        cmssw_command = ["cmsRun", "nano_config.py"] + input_files
        # actual payload:
        console.rule("Starting CMSSW")
        console.log("Command: {}".format(cmssw_command))
        with subprocess.Popen(
            cmssw_command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            bufsize=1,
            universal_newlines=True,
            env=my_env,
            cwd=workdir,
        ) as p:
            for line in p.stdout:
                if line != "\n":
                    console.log(line.replace("\n", ""))
            for line in p.stderr:
                if line != "\n":
                    console.log("stderr: {}".format(line.replace("\n", "")))
        if p.returncode != 0:
            console.log(f"Error when running {cmssw_command}")
            console.log("cmssw returned non-zero exit status {}".format(p.returncode))
            raise Exception("cmssw failed")
        else:
            console.log("Successful")
        console.log("Output files afterwards: {}".format(os.listdir(workdir)))
        outputfile.parent.touch()
        local_filename = os.path.join(workdir, "nanoAOD.root")
        outputfile.copy_from_local(local_filename)
        console.rule("Finished CMSSW")
