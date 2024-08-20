from RunCMSSW import RunCMSSW
from framework import console
import law
import yaml
import luigi
from law.task.base import WrapperTask


class ProduceNanoAOD(WrapperTask):
    """
    collective task to trigger ntuple production for a list of samples
    """

    sampledict = luigi.Parameter()
    production_tag = luigi.Parameter()
    silent = False

    def parse_sampledict(self, sampledict):
        try:
            with open(sampledict, "r") as f:
                samples = yaml.safe_load(f)
        except FileNotFoundError as e:
            console.error(f"Failed to load sample dict from {sampledict}")
            raise e
        return samples

    def flatten_sampledict(self, sampledict):
        # returns a list of samples, where each entry of the list is a dictionary like:
        # {"nick": "sample_nick", "era": "era", "sample_type": "type"}
        samples = []
        for era in sampledict:
            for type in sampledict[era]:
                for nick in sampledict[era][type]:
                    samples.append(
                        {
                            "nick": nick,
                            "era": era,
                            "sample_type": type,
                            "dasname": sampledict[era][type][nick],
                        }
                    )
        return samples

    def requires(self):
        data = self.flatten_sampledict(self.parse_sampledict(self.sampledict))
        if not self.silent:
            console.rule("")
            console.log(f"Production tag: {self.production_tag}")
            console.log(f"Number of samples: {len(data)}")
            console.rule("")
        self.silent = True

        requirements = {}
        for sample in data:
            requirements[f"CMSSW_{sample['nick']}"] = RunCMSSW(
                nick=sample["nick"],
                dasname=sample["dasname"],
                production_tag=self.production_tag,
                era=sample["era"],
                sample_type=sample["sample_type"],
            )
        return requirements

    def run(self):
        pass
