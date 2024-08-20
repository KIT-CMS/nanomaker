import luigi
import os
import json
import yaml
from framework import Task
from framework import console
from helpers.ReadFilelistFromDAS import read_filelist_from_das


def ensure_dir(file_path):
    directory = os.path.dirname(file_path)
    if not os.path.exists(directory):
        os.makedirs(directory)


class ConfigureDatasets(Task):
    """
    Gather information on the selected datasets, for now just mentioning an explicit dataset
    """

    nick = luigi.Parameter()
    dasname = luigi.Parameter()
    era = luigi.Parameter()
    sample_type = luigi.Parameter()
    production_tag = luigi.Parameter()
    silent = luigi.BoolParameter(default=False)

    def output(self):
        target = self.remote_target(
            f"sample_database/{self.nick}_{self.era}_{self.sample_type}.json"
        )
        return target

    def run(self):
        output = self.output()
        output.parent.touch()
        if not output.exists():
            output.parent.touch()
            xootd_prefix = "root://cms-xrd-global.cern.ch/"
            sample_data = read_filelist_from_das(
                self.nick,
                self.dasname,
                output,
                self.era,
                self.sample_type,
                xootd_prefix,
            )
            console.log()
            if not self.silent:
                console.log("Sample: {}".format(self.nick))
                console.log("Total Files: {}".format(sample_data["nfiles"]))
                console.log("Total Events: {}".format(sample_data["nevents"]))
                console.rule()
            output.dump(sample_data)
            console.log("Output written to {}".format(output.uri()))
