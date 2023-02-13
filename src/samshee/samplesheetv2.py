import re
import json
from collections import OrderedDict

from samshee.sectionedsheet import Settings, SectionedSheet, read_sectionedsheet, parse_sectionedsheet_from_json
from samshee.validation import validate, illuminasamplesheetv2schema, illuminasamplesheetv2logic

class SampleSheetV2:
    """A class that represents an illumina Sample Sheet v2.
    This is always constructed from a SectionedSheet that typically has been validated against a set of rules.
    """
    def __init__(self, secsheet: SectionedSheet = None, validation = [illuminasamplesheetv2schema, illuminasamplesheetv2logic]):
        """Parsing from """
        validate(secsheet, validation)
        self.validation = validation
        def secname(k):
            secsel = re.compile("^(.*)_(Settings|Data)$")
            m = re.match(secsel, k)
            if m is not None:
                return m.group(1)
            return None

        self.applications = OrderedDict()
        for key in secsheet.keys():
            sectionname = secname(key)
            if key.endswith("_Settings"):
                if sectionname not in self.applications:
                    self.applications[sectionname] = dict()
                self.applications[sectionname]['settings'] = secsheet[key]
            elif key.endswith("_Data"):
                if sectionname not in self.applications:
                    self.applications[sectionname]= dict()
                self.applications[sectionname]['data'] = secsheet[key]
            elif key == 'Header':
                self.header = Settings(secsheet['Header'])
            elif key == 'Reads':
                self.reads = secsheet['Reads']

    def to_sectionedsheet(self, validate_schema = True) -> SectionedSheet:
        """Constructs a SectionedSheet, unless validate_schema is False, the sheet is revalidated"""
        res = SectionedSheet(OrderedDict())
        if 'header' in self.__dict__.keys():
            res['Header'] = self.header
        if 'reads' in self.__dict__.keys():
            res['Reads'] = self.reads
        for appname, app in self.applications.items():
            if( 'settings' in app ):
                res[appname + "_Settings"] = app['settings']
            if( 'data' in app ):
                res[appname + "_Data"] = app['data']
        if validate_schema:
            validate(res, self.validation)
        return res

    def __str__(self) -> str:
        """returns a string representation of the sample sheet (adheres to the usual sample sheet format)"""
        return(str(self.to_sectionedsheet()))

    def write(self, filehandle) -> None:
        """writes a string representation of the sample sheet (adheres to the usual sample sheet format) to a file"""
        return self.to_sectionedsheet().write(filehandle)

    def to_json(self) -> str:
        return self.to_sectionedsheet().to_json()

def read_samplesheetv2(fromfile, validation = [illuminasamplesheetv2schema, illuminasamplesheetv2logic]) -> SampleSheetV2:
    """reads a SampleSheetv2 from a file by first parsing it as a SectionedSheet and then validating it against the standard schemata"""
    return SampleSheetV2(read_sectionedsheet(fromfile), validation = validation)

def parse_samplesheetv2_from_json(jsonstr : str, validation = [illuminasamplesheetv2schema, illuminasamplesheetv2logic]) -> SampleSheetV2:
    """parses a SampleSheetv2 from a json string by first parsing it as a SectionedSheet and then validating it against the standard schemata"""
    return SampleSheetV2(parse_sectionedsheet_from_json(jsonstr), validation)

def parse_samplesheetv2_from_object(obj, validation = [illuminasamplesheetv2schema, illuminasamplesheetv2logic]) -> SampleSheetV2:
    """constructs a SampleSheetv2 from a object (dict) by first constructing a SectionedSheet from it and then validating it against the standard schemata"""
    return parse_samplesheetv2_from_json(json.dumps(obj))
