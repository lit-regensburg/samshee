import re
from collections import OrderedDict

from ilsa2.sectionedsheet import Settings, SectionedSheet
from ilsa2.validation import validate, illuminasamplesheetv2schema, illuminasamplesheetv2logic

class SampleSheetV2:
    def __init__(self, secsheet: SectionedSheet = None, validation = [illuminasamplesheetv2schema, illuminasamplesheetv2logic]):
        validate(secsheet, validation)
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


    def to_sectionedsheet(self):
        res = SectionedSheet(OrderedDict())
        if 'header' in self.__dict__.keys():
            res['Header'] = self.header
        if 'Reads' in self.__dict__.keys():
            res['Reads'] = self.reads
        for appname, app in self.applications.items():
            if( 'settings' in app ):
                res[appname + "_Settings"] = app['settings']
            if( 'data' in app ):
                res[appname + "_Data"] = app['data']
        return res

    def __str__(self):
        return(str(self.to_sectionedsheet()))
