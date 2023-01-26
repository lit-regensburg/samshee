from pathlib import Path
from collections import OrderedDict
import typing
import re
from io import StringIO
import csv

"""A simple value type."""
ValueType = typing.NewType('ValueType', typing.Union[str,int,float])
"""A type that stores settings: Ordered key-value pairs"""
#Settings = OrderedDict[str,ValueType]
class Settings(OrderedDict[str, ValueType]):
    def __init__(self, init=OrderedDict()):
        super().__init__(init)

    def __str__(self) -> str:
        res = ""
        for key, value in self.items():
            res += f"{key},{value}\n"
        res += "\n\n"
        return res

"""A type data section"""
#Data = typing.NewType('Data', list)
class Data(list[dict]):
    def __init__(self, init=list()):
        super().__init__(init)

    def __str__(self) -> str:
       if(len(self) < 1):
           return ""
       res = StringIO("")
       fieldnames = self[0].keys()
       writer = csv.DictWriter(res, delimiter=",", fieldnames = fieldnames)
       writer.writeheader()
       for row in self:
           writer.writerow(row)
       return res.getvalue() + "\n\n"

"""any section"""
Section = typing.Union[Settings,Data]

"""A ordered dictionary of sections"""
class SectionedSheet(OrderedDict[str, Section]):
    def __init__(self, init):
        super().__init__(init)

    def __str__(self):
        res = ""
        for secname, secval in self.items():
            res += f"[{secname}]\n"
            res += str(secval)
        return(res)

    def write(self, filehandle):
        filehandle.write(str(self))



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
    res = Settings()
    for line in contents.split("\n"):
        (key, value) = line.rstrip(",").split(",")
        #try:
        res[key] = parse_value(value)
        #except ValueError as exc:
        #    raise InvalidValueType(exc)
    return res


def parse_data(contents: str) -> Data:
    return Data([row for row in csv.DictReader(StringIO(contents), delimiter=",", quotechar="\"")])


def parse_sectionedsheet(contents: str, explicitly_settings_section = ["header", "reads"]) -> SectionedSheet:
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
    with open(filename, "r") as f:
        return parse_sectionedsheet(f.read())

