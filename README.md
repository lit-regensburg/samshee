# Samshee

A schema-agnostic parser and writer for illumina® sample sheets v2 and similar documents.

## Features

- parsing and writing illumina® Sample Sheet v2 files.
- encoding to and parsing from json
- customizable validation, ships with a default validation schema that follows illumina® specs

## Examples

### Reading, modifying and writing
``` python
from samshee.samplesheetv2 import SampleSheetV2, read_samplesheetv2
sheet = read_samplesheetv2(filename)
print(sheet)

sheet.header['RunName'] = 'a_new_name'
with open(filename + '.new', "w") as fh:
    sheet.write(fh)
```

### Validation: Add validators when constructing the sample sheet:
``` python
from samshee.samplesheetv2 import SampleSheetV2, read_samplesheetv2
import samshee.validation
sheet = read_samplesheetv2(filename, validation = [
samshee.validation.illuminasamplesheetv2schema,
samshee.validation.illuminasamplesheetv2logic,
lambda doc: samshee.validation.check_index_distance(doc, 3)
])

sheet.applications['BCLConvert']['data'][0]['Index'] = 'ACTGACTG'
sheet.applications['BCLConvert']['data'][1]['Index'] = 'ACTGACTT'

# will fail, because check_index_distance will fail when exporting the sheet:
with open(filename + '.new', "w") as fh:
    sheet.write(fh)
```

This will give

``` 
Exception: anonymous validation function #2 raised validation error: Minimal index distance is 1 between the indices ACTGACTG and ACTGACTT which is less than the expected minimal index distance of 3
```

The first two validators (`illuminasamplesheetv2schema` and `illuminasamplesheetv2logic`) are highly recommended and are meant to enforce illumina® specifications so that the sample sheet is accepted by their tools.

## SectionedSheet
A sectioned sheet is a text file that contains one or more ordered sections in ini-file-like syntax. Every section starts with a section header, enclosed in square brackets, e.g. `[Reads]`. Any string on the same line after the section header is ignored.

Text following the line containing a section header until the start of a new section or EOF is part of the section.

Every section can either be a settings section, or a data section. Sections that end with "settings" or that are called "Header" or "Reads" are assumed to be settings by default. Any other section is assumed to be a data section.

A settings section is a set of key-value pairs, separated by a comma. Additional fields are ignored.

A data section is in CSV format with one header line, i.e. the first line of a data section determines the field names of the objects. Every row in the same section following the header defines one object with the fields given in the header.

A SectionedSheet is a relatively free format and no input validation other than what is absolutely necessary to parse a file is performed.

## SampleSheetV2
A SampleSheetV2 is a SectionedSheet that contains a defined set of sections and some required fields within these sections, see validation below. Every section that is not a "Header" or a "Reads" section refers to an "application" that may have settings or data sections, or both. The respective sections are named `[<Application>_Settings]` and `[<Application>_Data]`.


## Reading and writing
Use the functions `read_sectionedsheet` and `read_samplesheetv2`. Construction from strings is possible, too, use `parse_sectionedsheet` and `parse_samplesheetv2`.

Both SampleSheetV2 as well as SectionedSheet implement `__str__` and can be converted to a string using `str(sheet)`. Usually, the schema is revalidated at this point.

## Validation
Using `samshee.validation.validate`, `SectionedSheet`s can be validated using both json schema definitions and functions that may raise exceptions. The listed validators are processed one-by-one, i.e., if the SectionedSheet passes the first validator, it will be handed on to the next, etc. This means that validators later in the queue may make the assumptions that earlier validators have run successfully.

A SampleSheetV2 is constructed from a SectionedSheet that passes a sequence of validation steps. By default these are `illuminasamplesheetv2schema` and `illuminasamplesheetv2logic`. They are highly recommended and meant to enforce illumina® specifications so that the sample sheet is accepted by their tools. These validators are based on the [Sample Sheet v2 Settings document](https://support-docs.illumina.com/IN/NextSeq10002000/Content/SHARE/SampleSheetv2/SampleSheetValidation_fNS_m2000_m1000.htm) that provides admissible values and required fields for the `Header`, `Reads` settings as well as for the `Sequencing` and `BCLConvert` "Applications".

Validation of a sample sheet only happens at construction (unless `validators = None` or `[]`), but intentionally not when a sample sheet is manipulated to allow for intermediate states that would not pass validation (e.g. conflicting values for `Reads.Index1` and `BCLConvert.OverrideCycles`). However, by default, validation is performed when the sample sheet is rendered to a string or written out. This ensures that all output adheres to all listed validators.

Further custom validation beyond the illumina® spec can happen by json schema validation or calling a function with the SectionedSheet as an argument, i.e.

``` python
def my_validator(doc: SectionedSheet) -> None:
    if 'myapp' not in doc:
        raise Exception('sheet does not include settings for myapp.')
```

This would be equivalent to a json-schema

``` json
{
    "type": "object",
    "required": ["myapp"]
}
```

Much more complicated use cases are possible, enforcing naming conventions on samples, etc.

The following example would guarantee that the sample shield will adhere to illumina® standards and to our own defined schema (in this case that it has a section "myapp"):

``` python
from samshee import SectionedSheet, SampleSheetV2, read_sectionedsheet
from samshee.validation import illuminasamplesheetv2schema, illuminasamplesheetv2logic

def my_validation_function(sectionedsheet : SectionedSheet) -> None:
    # do checks here and raise exceptions.
    if 'myapp' not in doc:
        raise Exception('sheet does not include settings for myapp.')
    
my_schema = {} # any json schema
    
secsheet = read_sectionedsheet(filename)
samplesheet = SampleSheetV2(secsheet, validation = [illuminasamplesheetv2schema, illuminasamplesheetv2logic, my_validation_function, my_schema])
```

Json schemata must follow the [json-schema spec](https://json-schema.org/draft/2020-12/json-schema-validation.html), functions may perform any operations and are expected to raise exceptions if a SectionedSheet is invalid.
