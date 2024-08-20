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

    def requires(self):
        return LoadDatasetFromDAS(
            nick=self.nick,
            era=self.era,
            sample_type=self.sample_type,
            dasname=self.dasname,
        )

    def output(self):
        target = self.remote_target("sample_database/{}.json".format(self.nick))
        return target

    def load_filelist_config(self):
        # first check if a json exists, if not, check for a yaml
        sample_configfile_json = "sample_database/{era}/{type}/{nick}.json".format(
            era=self.era, type=self.sample_type, nick=self.nick
        )
        if os.path.exists(sample_configfile_json):
            with open(sample_configfile_json, "r") as stream:
                try:
                    sample_data = json.load(stream)
                except json.JSONDecodeError as exc:
                    print(exc)
                    raise Exception("Failed to load sample information")
        else:
            raise Exception("Failed to load sample information")
        return sample_data

    def run(self):
        output = self.output()
        output.parent.touch()
        if not output.exists():
            output.parent.touch()
            sample_data = self.load_filelist_config()
            if not self.silent:
                console.log("Sample: {}".format(self.nick))
                console.log("Total Files: {}".format(sample_data["nfiles"]))
                console.log("Total Events: {}".format(sample_data["nevents"]))
                console.rule()
            output.dump(sample_data)


class LoadDatasetFromDAS(Task):
    nick = luigi.Parameter()
    era = luigi.Parameter()
    sample_type = luigi.Parameter()
    dasname = luigi.Parameter()

    def output(self):
        return self.local_target(
            "sample_database/{era}/{type}/{nick}.json".format(
                era=self.era, type=self.sample_type, nick=self.nick
            )
        )

    def run(self):
        output = self.output()
        output.parent.touch()
        xootd_prefix = "root://cms-xrd-global.cern.ch/"
        read_filelist_from_das(
            self.nick, self.dasname, output, self.era, self.sample_type, xootd_prefix
        )
