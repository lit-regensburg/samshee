from pathlib import Path
from collections import OrderedDict
import typing
import re
from io import StringIO
import csv
import json

"""A simple value type."""
ValueType = typing.NewType('ValueType', typing.Union[str,int,float])

class Settings(OrderedDict[str, ValueType]):
    """A type that stores settings: Ordered key-value pairs"""
    def __init__(self, init=OrderedDict()):
        super().__init__(init)

    def __str__(self) -> str:
        res = ""
        for key, value in self.items():
            res += f"{key},{value}\n"
        res += "\n\n"
        return res

class Data(list[dict]):
    """A type that stores a Data section, i.e. a list of objects represented as named columns in a csv section"""
    def __init__(self, init=list()):
        super().__init__(init)

    def __str__(self) -> str:
       if(len(self) < 1):
           return ""
       res = StringIO("")
       fieldnames = self[0].keys()
       # TODO may specify a dialect.
       # currently, we have \r\n as lineterminator
       # this conflicts with terminators in other sections.
       writer = csv.DictWriter(res, delimiter=",", fieldnames = fieldnames)
       writer.writeheader()
       for row in self:
           writer.writerow(row)
       return res.getvalue() + "\n\n"

"""any section"""
Section = typing.Union[Settings,Data]

class SectionedSheet(OrderedDict[str, Section]):
    """A ordered dictionary of sections"""
    def __init__(self, init=OrderedDict()):
        super().__init__(init)

    def __str__(self) -> str:
        """A string representation of the SectionedSheet"""
        res = ""
        for secname, secval in self.items():
            res += f"[{secname}]\n"
            res += str(secval)
        return(res)

    def write(self, filehandle) -> None:
        """writes the sheet to a file"""
        filehandle.write(str(self))

    def to_json(self) -> str:
        """converts the sheet to a json string"""
        return json.dumps(self)



def parse_value(contents: str) -> ValueType:
    """parses a string to an admissible value in a settings section"""
    try:
        return int(contents)
    except:
        pass
    try:
        return float(contents)
    except:
        pass
    return contents.replace("\"", "")

def parse_settings(contents: str) -> Settings:
    """parses a string to a settings section (a key-value store)"""
    res = Settings()
    for i, line in enumerate(contents.split("\n")):
        unpacked = line.rstrip(",").split(",")
        # test if the key is meaningful, i.e. not from an empty line
        # the latter can happen in quoted sheets, where this corresponds to the last " before the next section
        if len(unpacked[0]) == 0 or unpacked[0] == "\"":
            continue
        elif len(unpacked) != 2:
            raise Exception(f"Malformed line #{i} {line}")
        key = unpacked[0].replace("\"", "")
        value = unpacked[1] # quoting in values is okay and prevents parsing as int / float
        res[key.replace("\"", "")] = parse_value(value)
    return res


def parse_data(contents: str) -> Data:
    """parses a string to a Data section, i.e. reads the section as named csv (first row is a header row)"""
    reader = csv.DictReader(StringIO(contents), delimiter=",", quotechar="\"")
    # skip empty rows
    return Data([row for row in reader if not all([row[i] is None or len(row[i])== 0 for i in row.keys()])])


def parse_sectionedsheet(contents: str, explicitly_settings_section = ["header", "reads"]) -> SectionedSheet:
    """parses string to a SectionedSheet, i.e. to an ordered dict of sections.
    by default, sections that are named "header" or "reads", or are suffixed "settings" are assumed to be settings sections.
    All others will be parsed as data sections
    """
    _section_pattern = re.compile(r"\[(\w*)\][^\n]*\n([^\[]*)")
    res = SectionedSheet(OrderedDict())
    for (name, content) in re.findall(_section_pattern, contents):
        if name.lower().endswith("settings") | (name.lower() in explicitly_settings_section):
            s = parse_settings(content.rstrip("\n "))
            res[name] = s
        else:
            res[name] = parse_data(content.rstrip("\n "))
    return res

def read_sectionedsheet(filename: typing.Union[Path,str]) -> SectionedSheet:
    """reads a file and parses it to a SectionedSheet"""
    with open(filename, "r") as f:
        return parse_sectionedsheet(f.read())

def parse_sectionedsheet_from_json(jsonstr: str, explicitly_settings_section = ["header", "reads"]) -> SectionedSheet:
    """parses a json string to a SectionedSheet"""
    a = json.loads(jsonstr, object_pairs_hook=OrderedDict)
    for k in a.keys():
        if (k.lower() in explicitly_settings_section) or (k.lower().endswith("settings")):
            a[k] = Settings(a[k])
        else:
            a[k] = Data(a[k])
    return SectionedSheet(a)

def parse_sectionedsheet_from_object(obj, explicitly_settings_section = ["header", "reads"]) -> SectionedSheet:
    """parses a object (e.g. read from json, or yaml, ...) to a SectionedSheet"""
    return parse_sectionedsheet_from_json(json.dumps(obj), explicitly_settings_section)
