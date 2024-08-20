import json
import subprocess


def read_filelist_from_das(nick, dasname, outputfile, era, type, xootd_prefix):
    print(f"Getting filelist for \n  Nick: {nick}")
    filedict = {}
    das_query = f"file dataset={dasname}"
    das_query += " instance=prod/global"
    print(f"  DAS Query: {das_query}")
    cmd = f"/cvmfs/cms.cern.ch/common/dasgoclient --query '{das_query}' --json"
    output = subprocess.Popen([cmd], shell=True, stdout=subprocess.PIPE)
    jsonS = output.communicate()[0]
    filelist = json.loads(jsonS)
    for file in filelist:
        filedict[file["file"][0]["name"]] = file["file"][0]["nevents"]
    data = {
        "nick": nick,
        "nfiles": len(filedict.keys()),
        "nevents": sum(filedict.values()),
        "era": era,
        "sample_type": type,
        "filelist": [f"{xootd_prefix}/{file}" for file in filedict.keys()],
    }
    return data
