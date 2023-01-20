from pathlib import Path
from collections import OrderedDict
import typing
import re
from io import StringIO
import pandas as pd

ValueType = typing.NewType('ValueType', typing.Union[str,int,float])
Settings = typing.NewType('Settings', OrderedDict[str,ValueType])
Data = typing.NewType('Data', pd.DataFrame)
Section = typing.Union[Settings,Data]
SectionedSheet = typing.NewType("SectionedSheet", OrderedDict[str,Section])

# sections that should be parsed as Settings even if their name is not suffixed with Settings:
_explicitly_settings_section = ['header', 'reads']

def parse_value(contents: str) -> ValueType:
    try:
        return int(contents)
    except:
        pass
    try:
        return float(contents)
    except:
        pass
    return contents

def parse_settings(contents: str) -> Settings:
    res = OrderedDict()
    for line in contents.split("\n"):
        (key, value) = line.split(",")
        #try:
        res[key] = parse_value(value)
        #except ValueError as exc:
        #    raise InvalidValueType(exc)
    return res

def parse_data(contents: str) -> Data:
    return pd.read_csv(StringIO(contents), sep=",")


def parse(contents: str) -> OrderedDict[str,str]:
    _section_pattern = re.compile(r"\[(\w*)\][^\n]*\n([^\[]*)")
    res = OrderedDict()
    for (name, content) in re.findall(_section_pattern, contents):
        if name.lower().endswith("_settings") | (name.lower() in _explicitly_settings_section):
            print(f"{name} is a Settings section")
            res[name] = parse_settings(content.rstrip("\n "))
        else:
            print(f"{name} is a Data section")
            res[name] = parse_data(content.rstrip("\n "))
    return res

def parse_file(filename: typing.Union[Path,str]) -> str:
    with open(filename, "r") as f:
        return parse(f.read())
