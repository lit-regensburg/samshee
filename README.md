# IlSa2

A schema-agnostic parser for illumina sample sheets v2 and similar documents.

## Examples

### Reading, modifying and writing
``` python
from ilsa2.samplesheetv2 import SampleSheetV2, read_samplesheetv2
sheet = read_samplesheetv2(filename)
sheet.header['RunName'] = 'a_new_name'
with open(filename + '.new', "w") as fh:
    sheet.write(fh)
```

### Validation: Add validators when constructing the sample sheet:
``` python
from ilsa2.samplesheetv2 import SampleSheetV2, read_samplesheetv2
import ilsa2.validation
sheet = read_samplesheetv2(filename, validation = [
ilsa2.validation.illuminasamplesheetv2schema,
ilsa2.validation.illuminasamplesheetv2logic,
lambda doc: ilsa2.validation.check_index_distance(doc, 3)
])

sheet.applications['BCLConvert']['data'][0]['Index'] = 'ACTGACTG'
sheet.applications['BCLConvert']['data'][1]['Index'] = 'ACTGACTT'

# will fail, because check_index_distance will fail when exporting the sheet:
with open(filename + '.new', "w") as fh:
    sheet.write(fh)
```

This will give

``` 
Exception: Minimal index distance is 1 which is less than the expected minimal index distance of 3
```

The first two validators (`illuminasamplesheetv2schema` and `illuminasamplesheetv2logic`) are highly recommended and are meant to enforce illumina specifications so that the sample sheet is accepted by their tools.

## SectionedSheet
A sectioned sheet is a text file that contains one or more ordered sections. Every section starts with a section header, enclosed in square brackets, e.g. `[Reads]`. Any string on the same line after the section header is ignored.

Text following the line containing a section header until the start of a new section or EOF is part of the section.

Every section can either be a settings section, or a data section. Sections that end with "settings" or are called "Header" or "Reads" are assumed to be settings by default. Any other section is assumed to be a data section.

A settings section is a set of key-value pairs, separated by a comma. Additional fields are ignored.

A data section is in CSV format with one header line, i.e. the first line of a data section determines the field names of the objects. Every row in the same section following the header defines one object with the fields given in the header.

## SampleSheetV2
A SampleSheetV2 is a SectionedSheet that contains a defined set of sections. Every section that is not a "Header" or a "Reads" section refers to an "application" that may have settings or data sections, or both. The respective sections are named `[<Application>_Settings]` and `[<Application>_Data]`.

## Reading and writing

## Validation
Admissible values and required fields for the `Header`, `Reads` settings as well as for the `Sequencing` and `BCLConvert` "Applications" are given in the illumina document
[Sample Sheet v2 Settings](https://support-docs.illumina.com/IN/NextSeq10002000/Content/SHARE/SampleSheetv2/SampleSheetValidation_fNS_m2000_m1000.htm).

Generally parsing in this library is agnostic. Input must only adhere to the SectionedSheet spec given above. Further validation can happen by json schema validation or calling a function with the SectionedSheet as an argument, i.e.

``` python
def my_validator(doc: SectionedSheet) -> None:
    if 'myapp' not in doc:
        raise Exception('sheet does not include settings for myapp.')
    pass
```

This would be equivalent to a json-schema

``` json
{
    "type": "object",
    "required": ["myapp"]
}
```

By default the only the requirements in the illumina document above are checked. Additional checks on the SectionedSheet can be performed when constructing the SampleSheet, by including any schema or function in the `validation` array (see also the examples at the beginning of this document):

``` python
from ilsa2 import SectionedSheet, SampleSheetV2, read_sectionedsheet
from ilsa2.validation import illuminasamplesheetv2schema, illuminasamplesheetv2logic

def my_validation_function(sectionedsheet : SectionedSheet) -> None:
    # do checks here and raise exceptions.
    pass
    
my_schema = {} # any json schema
    
secsheet = read_sectionedsheet(filename)
samplesheet = SampleSheetV2(secsheet, validation = [illuminasamplesheetv2schema, illuminasamplesheetv2logic, my_validation_function, my_schema])
```

Schemata must adhere to the [json-schema spec](https://json-schema.org/draft/2020-12/json-schema-validation.html), functions may perform any operations and are expected to raise exceptions if a SectionedSchema is invalid. Validation happens in the order given in the list, so any schema or validation function that comes after another can assume that the objects validates successfully against the former (e.g. that every SectionedSheet in the example above is a valid illumina SampleSheet v2). This can be used to implement own conventions, naming schemes, etc.

Example: Checking for a minimal distance between indices can be done using the `check_index_distance` in `ilsa2.validation`:

``` python
from ilsa2.validation import illuminasamplesheetv2schema, illuminasamplesheetv2logic, nextseq1k2kschema, check_index_distance
samplesheet = SampleSheetV2(secsheet, validation = [
    illuminasamplesheetv2schema, 
    illuminasamplesheetv2logic, 
    lambda doc : check_index_distance(doc, 3)
    ])
```

This will check if the document is a illumina sample sheet v2 **and** if the indices have a minimal index distance of 3.

