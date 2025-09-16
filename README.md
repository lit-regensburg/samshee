# Samshee

A schema-agnostic parser and writer for illumina® sample sheets v2 and similar documents.

## Features

- parsing and writing illumina® Sample Sheet v2 files.
- encoding to and parsing from json
- customizable validation, ships with a default validation schema that follows illumina® specs

## Installation

Samshee is on [pypi](https://pypi.org/project/samshee/), so you can simply
```
pip install samshee
```

For development, clone the repository and
```
pip install -e .
```

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
SamsheeValidationException: anonymous validation function #2 raised validation error: Minimal index distance is 1 between the indices ACTGACTG and ACTGACTT which is less than the expected minimal index distance of 3
```

The first two validators (`illuminasamplesheetv2schema` and `illuminasamplesheetv2logic`) are highly recommended and are meant to enforce illumina® specifications so that the sample sheet is accepted by their tools.

See "Validation" below for valid arguments for `validation`.


### Command line usage
A sample sheet can also be linted and validated with the command line interface, 

``` bash
python -m samshee SampleSheet.csv
```

This will simply read the sample sheet, check if there are any errors and output it again in a normalized form, so it may also be useful to format samplesheets consistently (use `python -m samshee SampleSheet.csv > SampleSheet_formatted.csv`)

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

A SampleSheetV2 is constructed from a SectionedSheet that passes a sequence of validation steps. By default these are `illuminasamplesheetv2schema` and `illuminasamplesheetv2logic`. They are highly recommended and meant to enforce illumina® specifications so that the sample sheet is accepted by their tools. These validators are based on the [Sample Sheet v2 Settings document](https://help.connected.illumina.com/run-set-up/overview/instrument-settings/nextseq-1000-2000-settings) that provides admissible values and required fields for the `Header`, `Reads` settings as well as for the `Sequencing` and `BCLConvert` "Applications" (other applications / sections are unimplemented).

Validation of a sample sheet only happens at construction (unless `validators = None` or `[]`), but intentionally not when a sample sheet is manipulated to allow for intermediate states that would not pass validation (e.g. conflicting values for `Reads.Index1` and `BCLConvert.OverrideCycles`). However, by default, validation is performed when the sample sheet is rendered to a string or written out. This ensures that all output adheres to all listed validators.

Further custom validation beyond the illumina® spec can happen by json schema validation or calling a function with the SectionedSheet as an argument and raising `SamsheeValidationException` in the case of an invalid sheet, i.e.

``` python
from samshee.validation import  SamsheeValidationException
def my_validator(doc: SectionedSheet) -> None:
    if 'myapp' not in doc:
        raise SamsheeValidationException('sheet does not include settings for myapp.')
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
from samshee.validation import illuminasamplesheetv2schema, illuminasamplesheetv2logic, SamsheeValidationException

def my_validation_function(sectionedsheet : SectionedSheet) -> None:
    # do checks here and raise exceptions.
    if 'myapp' not in doc:
        raise SamsheeValidationException('sheet does not include settings for myapp.')
    
my_schema = {} # any json schema
    
secsheet = read_sectionedsheet(filename)
samplesheet = SampleSheetV2(secsheet, validation = [illuminasamplesheetv2schema, illuminasamplesheetv2logic, my_validation_function, my_schema])
```

Json schemata must follow the [json-schema spec](https://json-schema.org/draft/2020-12/json-schema-validation.html), functions may perform any operations and are expected to raise exceptions if a SectionedSheet is invalid.

It is also possible to refer to schemata, e.g. `{"$ref": "urn:samshee:illuminav2/v1"}` is equivalent to passing `illuminasamplesheetv2schema` for validating against the built-in schema. For referencing an externally hosted schema, use resolvable URLs, e.g. `{"$ref": "https://dataportal.lit.eu/schemas/litngscoresamplesheet/v0.1/litngscoresamplesheet.schema.json"}` will check against the schema that we use in the LIT NGS Core.

## Commandline tool
Samshee comes with a simple command line tool that does nothing more than (1) reading a sectioned sheet (either in normal text or json form), (2) possibly validates it and (3) prints it. This can be used for linting, format conversions or validating sheets on the command line.

### in- and output

The output is always printed to stdout that can be redirected to a file. If the input sheet should be read from stdin, the special filename `-` must be used:

``` bash
cat test.csv | python -m samshee -
# equivalent to
python -m samshee test.csv
```

### Return codes
If no errors occur, samshee will exit with exit code `0` and print the sheet in the desired output. If any of the steps produces an error, the return code indicates which step generated the error:

| exit code | cause                                                                                             |
|-----------|---------------------------------------------------------------------------------------------------|
| `1`       | error reading the input sheet                                                                     |
| `2`       | validation error (with explicit validation rules, e.g. `--schema`)                                |
| `3`       | unknown input or output format. Check `--help`                                                    |
| `4`       | error during output generation (may be validation error if the output format requires validation) |


### Converting between formats

To convert a sample sheet to json, simply specify the output format:
``` bash
python -m samshee --output-format json test.csv
```

An interesting application of this is to easily extract information from a sheet, e.g. with [jq](https://jqlang.github.io/jq/):

``` bash
python -m samshee --output-format json test.csv | jq '.["Reads"]["Read1Cycles"]+.["Reads"]["Read2Cycles"]'
# will print the total read length (without indices)
```

Supported formats are the following:

| format      | input       | output      | description                                                              |
|-------------|-------------|-------------|--------------------------------------------------------------------------|
| `sectioned` | ✓ (default) | ✓           | Sectioned format (see above), common to v1 and v2 samplesheets.          |
| `v2`        | ✗           | ✓ (default) | Sectioned format that requires successful validation for v2 samplesheets |
| `json`      | ✓           | ✓           | machine readable json format                                             |

If the input is not a sectioned sheet, but a json file (to convert back), this must be stated explicitly as well:
``` bash
python -m samshee --input-format json test.json
```

### Schema validation
Samshee allows to validate against an external (json) schema given as argument, e.g., to check if there is a section `Data`, one could do
``` bash
python -m samshee --schema '{"required": ["Data"]}' test.csv
```

Note that this does **not** bypass any validation that is done during printing the output, e.g., if the output prints to a v2 samplesheet (the default), the schema `urn:samshee:illuminav2/v1` is checked regardless of the schema option. To circumvent this, explicitly state `sectioned` as output format (which is not validated):
``` bash
python -m samshee --schema '{"required": ["Data"]}' --output-format sectioned test.csv
```

Several schemas can simply be chained:
``` bash
python -m samshee --schema '{"$ref": "urn:samshee:illuminav2/v1"}' --schema '{"required": ["BCLConvert_Data"]}' --output-format sectioned test.csv
```
This example will first check if the illuminav2 schema is fulfilled and then if a `BCLConvert_Data` section is present.

#### Schema files

The `--schema` option only accepts json schema input, but no file names. To read from a json schema file, the file has to be referenced (and specify its schema definition). For example, we could have a schema file `test.schema.json` that checks for the presence of `RunName` in the `Header` section:

``` json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "properties": {
     "Header": {
        "type": "object",
        "required": ["RunName"]
     }
  }
}
```

To use this schema, we have to reference it in the samshee call:
``` bash
python -m samshee --schema '{"$ref": "file:./test.schema.json"}' test.csv
```

#### Remote schemas

Schema definitions can also be retrieved automatically from a remote URL. The following example will check if the test sheet is a v2 sample sheet (because it is the default output) that also fulfills conventions in place at the NGS Core of the [LIT](https://lit.eu):

``` bash
python -m samshee --schema '{"$ref": "https://dataportal.lit.eu/schemas/litngscoresamplesheet/v0.1/litngscoresamplesheet.schema.json"}' test.csv
```
