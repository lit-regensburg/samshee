from pathlib import Path
from collections import OrderedDict
from typing import TypeAlias, Union
import re
from io import StringIO, IOBase, TextIOWrapper, TextIOBase
import csv
import json
import itertools

"""A simple value type."""
ValueType: TypeAlias = Union[str, int, float, bool]


class Settings(OrderedDict[str, ValueType]):
    """A type that stores settings: Ordered key-value pairs"""

    def __init__(self, init=OrderedDict()) -> None:
        assert isinstance(init, dict), "Settings: init argument is not a dict"
        assert all(
            [not isinstance(o, dict) for o in init.values()]
        ), "Settings: init argument does contain dicts (only simple values allowed)"
        super().__init__(init)

    def __str__(self) -> str:
        res = ""
        res = StringIO("")
        writer = csv.DictWriter(
            res, fieldnames=["key", "value"], delimiter=",", quoting=csv.QUOTE_MINIMAL
        )
        for k, v in self.items():
            writer.writerow({"key": k, "value": v})
        return str(res.getvalue() + "\n\n")


class Data(list[dict]):
    """A type that stores a Data section, i.e. a list of objects represented as named columns in a csv section"""

    def __init__(self, init=list()) -> None:
        assert isinstance(init, list), "Data: init argument is not a list."
        super().__init__(init)

    def __str__(self) -> str:
        if len(self) < 1:
            return ""
        res = StringIO("")
        fieldnames = self[0].keys()
        # TODO may specify a dialect.
        # currently, we have \r\n as lineterminator
        # this conflicts with terminators in other sections.
        writer = csv.DictWriter(
            res, delimiter=",", fieldnames=fieldnames, quoting=csv.QUOTE_MINIMAL
        )
        writer.writeheader()
        for row in self:
            writer.writerow(row)
        return res.getvalue() + "\n\n"


class Array(list[ValueType]):
    """A type that stores an array of values (e.g. sample sheet v1 Settings sections)"""

    def __init__(self, init=list()) -> None:
        if len(init) > 0:
            dtype = type(init[0])
            assert all(
                [isinstance(o, dtype) for o in init]
            ), "Array: Array is not uniformly typed (mixed data types)"
        super().__init__(init)

    def __str__(self) -> str:
        res = ""
        for value in self:
            if isinstance(value, str):
                res += f'"{value}"\n'
            else:
                res += f"{value}\n"
        res += "\n\n"
        return res


"""any section"""
Section: TypeAlias = Union[Settings, Data, Array]


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
        return res

    def write(self, filehandle) -> None:
        """writes the sheet to a file"""
        filehandle.write(str(self))

    def to_json(self, pretty=False) -> str:
        """converts the sheet to a json string"""
        if pretty:
            return json.dumps(self, indent=4)
        else:
            return json.dumps(self)


def attempt_cast(value: str) -> ValueType:
    try:
        return int(value)
    except:
        pass
    try:
        return float(value)
    except:
        pass
    return value


def parse_value(contents: str) -> ValueType:
    """parses a string to an admissible value in a settings section"""
    return attempt_cast(contents)


def parse_settings(contents: str) -> Settings:
    """parses a string to a settings section (a key-value store)"""
    if contents.lstrip("\n\r ") == "":
        return Settings()
    peaker, reader = itertools.tee(
        csv.reader(
            StringIO(contents.lstrip("\n\r ")),
            delimiter=",",
            quotechar='"',
            quoting=csv.QUOTE_MINIMAL,
        )
    )
    # get number of columns
    ncols = len([field for field in next(peaker) if field != ""])
    del peaker
    if ncols != 2:
        raise ValueError(
            "string cannot be parsed into Settings, because it is not a two-columns section."
        )

    d = Settings(
        OrderedDict(
            [(str(row[0]), parse_value(row[1])) for row in reader if row[0] != ""]
        )
    )
    return d


#
#   for i, line in enumerate(contents.split("\n")):
#       unpacked = line.rstrip(",").split(",")
#       # test if the key is meaningful, i.e. not from an empty line
#       # the latter can happen in quoted sheets, where this corresponds to the last " before the next section
#       if len(unpacked[0]) == 0 or unpacked[0] == '"':
#           continue
#       elif len(unpacked) != 2:
#           raise Exception(f"Malformed line #{i} {line}")
#       key = unpacked[0].replace('"', "")
#       value = unpacked[
#           1
#       ]  # quoting in values is okay and prevents parsing as int / float
#       res[key.replace('"', "")] = parse_value(value)
#   return res


def parse_data(contents: str) -> Data:
    """parses a string to a Data section, i.e. reads the section as named csv (first row is a header row)"""
    reader = csv.DictReader(
        StringIO(contents.lstrip("\n\r ")), delimiter=",", quotechar='"'
    )
    # skip empty rows
    d = Data(
        [
            row
            for row in reader
            if not all(
                [row[i] is None or len(row[i]) == 0 for i in row.keys()]
            )  # and not any([key == '' for key in row.keys()])
        ]
    )
    # remove fields that have an empty name (e.g. from trailing commas at line end):
    if len(d) < 1:
        raise ValueError("no content in Data Section")
    empty_fields = [x for x in d[0].keys() if re.match(r"^\s*$", x)]
    for e in d:
        for field in empty_fields:
            del e[field]

    # Cast values that look like int/float from string
    for item in d:
        item.update((k, attempt_cast(v)) for k, v in item.items())

    return d


def parse_array(contents: str) -> Array:
    """parses an Array section, i.e. every line is one value, no header, other fields are ignored"""
    peaker, reader = itertools.tee(
        csv.reader(StringIO(contents.lstrip("\n\r ")), delimiter=",", quotechar='"')
    )
    # get number of columns
    ncols = len([field for field in next(peaker) if field != ""])
    del peaker

    if ncols != 1:
        raise ValueError(
            "string cannot be parsed into Array, because it is not a single column section."
        )

    is_header_re = re.compile(r"^\[.*\]$")
    d = Array(
        [
            parse_value(row[0])
            for row in reader
            if len(row) > 0 and row[0] != "" and not re.match(is_header_re, row[0])
        ]
    )
    return d


def parse_anything(sectionname: str, contents: str) -> ValueType:
    """parses an section and tries to guess the section type.
    if section names end with "settings" or "data", Settings and Data sections are assumed, respectively.
    for sections that do not end in this way, everything is tried out and the section type will be whatever matches first of Settings, Data, Array (in this order)
    """
    if sectionname.lower().endswith("settings"):
        return parse_settings(contents)
    elif sectionname.lower().endswith("data"):
        return parse_data(contents)
    else:
        try:
            return parse_settings(contents)
        except:
            pass
        try:
            return parse_data(contents)
        except:
            pass
        try:
            return parse_array(contents)
        except:
            pass
        raise ValueError("Cannot guess section type")


def parse_sectionedsheet(contents: str) -> SectionedSheet:
    """parses string to a SectionedSheet, i.e. to an ordered dict of sections.
    by default, sections that are named "header" or "reads", or are suffixed "settings" are assumed to be settings sections.
    All others will be parsed as data sections
    """
    _section_pattern = re.compile(r"\[(\w*)\][^\n]*\n([^\[]*)")
    res = SectionedSheet(OrderedDict())
    for name, content in re.findall(_section_pattern, contents):
        try:
            res[name] = parse_anything(name, content.rstrip("\n "))
        except Exception as exc:
            raise Exception(f"Error parsing section {name}: {exc}")
    return res


def read_sectionedsheet(file: Union[Path, str, IOBase]) -> SectionedSheet:
    """reads a file and parses it to a SectionedSheet"""
    if isinstance(file, TextIOBase):
        return parse_sectionedsheet(file.read())
    elif isinstance(file, IOBase):
        return parse_sectionedsheet(TextIOWrapper(file).read())
    with open(file, "r") as f:
        return parse_sectionedsheet(f.read())


def guess_section_from_object(obj: dict) -> ValueType:
    try:
        return Settings(obj)
    except:
        pass
    try:
        return Data(obj)
    except:
        pass
    try:
        return Array(obj)
    except:
        raise ValueError("Cannot guess section type")


def parse_sectionedsheet_from_json(jsonstr: str) -> SectionedSheet:
    """parses a json string to a SectionedSheet"""
    a = json.loads(jsonstr, object_pairs_hook=OrderedDict)
    for k in a.keys():
        if k.lower().endswith("settings"):
            a[k] = Settings(a[k])
        elif k.lower().endswith("data"):
            a[k] = Data(a[k])
        else:
            a[k] = guess_section_from_object(a[k])
    return SectionedSheet(a)


def parse_sectionedsheet_from_object(obj) -> SectionedSheet:
    """parses a object (e.g. read from json, or yaml, ...) to a SectionedSheet"""
    return parse_sectionedsheet_from_json(json.dumps(obj))
