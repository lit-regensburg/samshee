from pathlib import Path
from collections import OrderedDict
import typing
import re
from io import StringIO
import csv

"""A simple value type."""
ValueType = typing.NewType('ValueType', typing.Union[str,int,float])
"""A type that stores settings: Ordered key-value pairs"""
Settings = typing.NewType('Settings', OrderedDict[str,ValueType])
"""A type data section"""
Data = typing.NewType('Data', list)
"""any section"""
Section = typing.Union[Settings,Data]
"""A ordered dictionary of sections"""
SectionedSheet = typing.NewType("SectionedSheet", OrderedDict[str,Section])

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

def settings_to_string(settings: Settings) -> str:
    res = ""
    for key in settings:
        res += f"{key},{settings[key]}\n"
    res += "\n\n"
    return res

def parse_data(contents: str) -> Data:
    return [row for row in csv.DictReader(StringIO(contents), delimiter=",", quotechar="\"")]

def data_to_string(data: Data) -> str:
    if(len(data) < 1):
        return ""
    res = StringIO("")
    fieldnames = data[0].keys()
    writer = csv.DictWriter(res, delimiter=",", fieldnames = fieldnames)
    writer.writeheader()
    for row in data:
        writer.writerow(row)
    return res.getvalue() + "\n\n"

def parse_sectionedsheet(contents: str, explicitly_settings_section = ["header", "reads"]) -> SectionedSheet:
    _section_pattern = re.compile(r"\[(\w*)\][^\n]*\n([^\[]*)")
    res = SectionedSheet(OrderedDict())
    for (name, content) in re.findall(_section_pattern, contents):
        if name.lower().endswith("_settings") | (name.lower() in explicitly_settings_section):
            s = parse_settings(content.rstrip("\n "))
            res[name] = s
        else:
            res[name] = parse_data(content.rstrip("\n "))
    return res

def read_sectionedsheet(filename: typing.Union[Path,str]) -> SectionedSheet:
    with open(filename, "r") as f:
        return parse_sectionedsheet(f.read())
