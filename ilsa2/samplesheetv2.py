from ilsa2.sectionedsheet import SectionedSheet
from jsonschema import validate

# a schema that validates a sectioned sheet to be a samplesheet
# we will put this elsewhere, but for now this is the place:
# this follows
# https://support-docs.illumina.com/IN/NextSeq10002000/Content/SHARE/SampleSheetv2/SampleSheetValidation_fNS_m2000_m1000.htm
# (which is not a proper spec, but reasonably close to it and this is my interpretation)
samplesheetv2schema = {
    "type": "object",
    "required": ["Header", "Reads", "Sequencing_Settings"],
    "properties": {
        "Header": {
            "type": "object",
            "required": ["FileFormatVersion"],
            "properties": {
                "FileFormatVersion": {
                    "type": "integer",
                    "const": 2
                },
                "RunName": {
                    "type": "string",
                    "pattern": "^[a-zA-Z0-9_\-\.]*$",
                    "description": "Unique run name of your preference. The RunName can contain alphanumeric characters, underscores, dashes, and periods. If the RunName contains spaces or special characters, analysis fails."
                },
                "RunDescription": {
                    "type": "string",
                    "description": "Description of the run"
                },
                "Instrument Type": {
                    "type": "string",
                    "description": "The instrument name",
                    "example": ["NextSeq 1000", "NextSeq 2000"]
                },
                "InstrumentPlatform": {
                    "type": "string",
                    "description": "The instrument platform name",
                    "example": ["NextSeq 1000", "NextSeq 2000"]
                }
            }
        },
        "Reads": {
            "type": "object",
            "required": ["Read1Cycles"],
            "properties": {
                "Read1Cycles": {
                    "type": "integer",
                    "minimum": 1,
                    "description": "Number of cycles in the first read. Ideally, this value should be 26 or greater. However, you can proceed with fewer cycles. If OverrideCycles is present in the [BCLConvert_Settings] section, this value must be consistent with the sum of the Read1 section of OverrideCycles."
                },
                "Read2Cycles": {
                    "type": "integer",
                    "minimum": 1,
                    "description": "Number of cycles in the second read. Required when running a paired-end sequencing run. Required if Custom Read 2 Primer is set to true on the UI. If OverrideCycles is present in the [BCLConvert_Settings] section, this value must be consistent with the sum of the Read 2 section of OverrideCycles. Ideally, this value should be 26 or greater. However, you can proceed with fewer cycles."
                },
                "Index1Cycles": {
                    "type": "integer",
                    "minimum": 1,
                    "description": "Number of cycles in the first Index Read. Required when sequencing more than one sample. If OverrideCycles is present in the [BCLConvert_Settings] section, this value must be consistent with the sum of the Index 1 section of OverrideCycles."
                },
                "Index2Cycles": {
                    "type": "integer",
                    "minimum": 1,
                    "description": "Number of cycles in the first Index Read. Required when sequencing more than one sample. If OverrideCycles is present in the [BCLConvert_Settings] section, this value must be consistent with the sum of the Index 2 section of OverrideCycles."
                }
            }
        },
        "Sequencing_Settings": {
            "type": "object",
            "required": [],
            "properties": {
                "LibraryPrepKits": {
                    "type": "string",
                    "description": "Your library prep kit. Only one library prep kit is allowed."
                }
            }
        },
        "BCLConvert_Settings": {
            "type": "object",
            "required": ["SoftwareVersion"],
            "properties": {
                "AdapterRead1": {
                    "type": "string",
                    "pattern": "^[ACGT]+",
                    "description": "The sequence to trim or mask from the end of Read 1. AdapterRead1 trims cycles by default. Value must be <= Read1Cycles."
                },
                "AdapterRead2": {
                    "type": "string",
                    "pattern": "^[ACGT]+",
                    "description": "The sequence to trim or mask from the end of Read 2. AdapterRead2 trims cycles by default. Value must be <= Read2Cycles."
                },
                "BarcodeMismatchesIndex1": {
                    "type": "integer",
                    "minimum": 0,
                    "maximum": 2,
                    "default": 1,
                    "description": "The number of allowed mismatches between the first Index Read and index sequence. Only required if Index1Cycles is specified."
                },
                "BarcodeMismatchesIndex2": {
                    "type": "integer",
                    "minimum": 0,
                    "maximum": 2,
                    "default": 1,
                    "description": "The number of allowed mismatches between the first Index Read and index sequence. Only required if Index2Cycles is specified."
                },
                "FastqCompressionFormat": {
                    "type": "string",
                    "enum": ["dragen", "gzip"]
                },
                "OverrideCycles": {
                    "type": "string",
                    "pattern": "^([NYIU][0-9]+;?){1,}$"
                },
                "SoftwareVersion": {
                    "type": "string",
                    "pattern": "^[0-9]+\.[0-9]+\.[0-9]+.*"
                }
            },
            "BCLConvert_Data": {
                "type": "object",
                "required": ["Sample_ID"],
                "properties": {
                    "Sample_ID": {
                        "type": "string",
                        "pattern": "^[a-zA-Z0-9\-_]+$",
                        "maxLength": 20,
                        "description": "The ID of the sample. Separate each identifier with a dash or underscore.",
                        "examples": ["Sample1-DQB1-022515"]
                    },
                    "Index": {
                        "type": "string",
                        "pattern": "^[ACTG]+$",
                        "description": "The index sequence associated with the sample. Required when sequencing more than one sample."
                    },
                    "Index2": {
                        "type": "string",
                        "pattern": "^[ACTG]+$",
                        "description": "The second index sequence associated with the sample. Make sure the second index (i5) adapter sequences are in forward orientation. DRAGEN automatically reverse complements i5 indexes during secondary analysis."
                    },
                    "Lane": {
                        "type": "integer",
                        "minimum": 0,
                        "description": "The lane of the flow cell. Lanes are represented by one integer value."
                    },
                    "Sample_Project": {
                        "type": "string",
                        "pattern": "^[a-zA-Z0-9\-_]+$",
                        "maxLength": 20
                    }
                }
            }
        }
    }

}

bclconvertschema = {
}

nextseq1k2kschema = {
    "type": "object",
    "required": ["Header", "Reads"],
    "properties": {
        "Reads": {
            "type": "object",
            "properties": {
                "Index1Cycles": {
                    "maximum": 10
                },
                "Index2Cycles": {
                    "maximum": 10
                },
            }
        }
    }
}

class SampleSheetV2:
    def __init__(self, secsheet: SectionedSheet):
        validate(instance=secsheet, schema=samplesheetv2schema)
        self.header = secsheet['Header']
        self.reads = secsheet['Reads']
        # everything else is an application:
