from jsonschema import validate
import re
from collections import OrderedDict
import types

from ilsa2.sectionedsheet import SectionedSheet, settings_to_string, data_to_string
from ilsa2.validation import illuminasamplesheetv2schema, illuminasamplesheetv2logic

class SampleSheetV2:
    def __init__(self, secsheet: SectionedSheet, validation = [illuminasamplesheetv2schema, illuminasamplesheetv2logic]):
        if validation is None:
            schemata = []
        elif type(validation) == list:
            pass
        else:
            validation = [validation]

        for schema in validation:
            if(type(schema) == dict):
                validate(instance=secsheet, schema=schema)
            elif(type(schema) == types.FunctionType):
                schema(secsheet)

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
                self.header = secsheet['Header']
            elif key == 'Reads':
                self.reads = secsheet['Reads']

    def to_string(self):
        res = ""
        if 'header' in self.__dict__.keys():
            res += '[Header]\n'
            res += settings_to_string(self.header)
        if 'Reads' in self.__dict__.keys():
            res += '[Reads]\n'
            res += settings_to_string(self.reads)
        for appname, app in self.applications.items():
            if 'settings' in app:
                res += f"[{appname}_Settings]\n"
                res += settings_to_string(app['settings'])
            if 'data' in app:
                res += f"[{appname}_Data]\n"
                res += data_to_string(app['data'])
        return(res)
