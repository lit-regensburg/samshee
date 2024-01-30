import itertools
import re
from typing import Callable, cast, Mapping, Tuple, Optional

from jsonschema import Draft202012Validator
from jsonschema.exceptions import ErrorTree, best_match

from samshee.sectionedsheet import SectionedSheet, Settings, Data

from referencing import Registry, Resource
import requests
import referencing.retrieval


@referencing.retrieval.to_cached_resource()
def cached_retrieve_via_http(uri):
    return requests.get(uri).text


registry = Registry(retrieve=cached_retrieve_via_http)


#
# a schema that validates a sectioned sheet to be a samplesheet
# this follows
# https://support-docs.illumina.com/IN/NextSeq10002000/Content/SHARE/SampleSheetv2/SampleSheetValidation_fNS_m2000_m1000.htm
# (which is not a proper spec, but reasonably close to it and this is my interpretation)
illuminasamplesheetv2schema = {
    "$id": "urn:samshee:illuminav2/v1",
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "illumina SampleSheetv2 schema spec",
    "type": "object",
    "required": ["Header", "Reads"],
    "properties": {
        "Header": {
            "type": "object",
            "required": ["FileFormatVersion"],
            "properties": {
                "FileFormatVersion": {"type": "integer", "const": 2},
                "RunName": {
                    "type": "string",
                    "pattern": r"^[-a-zA-Z0-9_\.]*$",
                    "description": "Unique run name of your preference. The RunName can contain alphanumeric characters, underscores, dashes, and periods. If the RunName contains spaces or special characters, analysis fails.",
                },
                "RunDescription": {
                    "type": "string",
                    "description": "Description of the run",
                },
                "Instrument Type": {
                    "type": "string",
                    "description": "The instrument name",
                    "example": ["NextSeq 1000", "NextSeq 2000"],
                },
                "InstrumentPlatform": {
                    "type": "string",
                    "description": "The instrument platform name",
                    "example": ["NextSeq 1000", "NextSeq 2000"],
                },
            },
        },
        "Reads": {
            "type": "object",
            "required": ["Read1Cycles"],
            "properties": {
                "Read1Cycles": {
                    "type": "integer",
                    "minimum": 1,
                    "description": "Number of cycles in the first read. Ideally, this value should be 26 or greater. However, you can proceed with fewer cycles. If OverrideCycles is present in the [BCLConvert_Settings] section, this value must be consistent with the sum of the Read1 section of OverrideCycles.",
                },
                "Read2Cycles": {
                    "type": "integer",
                    "minimum": 1,
                    "description": "Number of cycles in the second read. Required when running a paired-end sequencing run. Required if Custom Read 2 Primer is set to true on the UI. If OverrideCycles is present in the [BCLConvert_Settings] section, this value must be consistent with the sum of the Read 2 section of OverrideCycles. Ideally, this value should be 26 or greater. However, you can proceed with fewer cycles.",
                },
                "Index1Cycles": {
                    "type": "integer",
                    "minimum": 1,
                    "description": "Number of cycles in the first Index Read. Required when sequencing more than one sample. If OverrideCycles is present in the [BCLConvert_Settings] section, this value must be consistent with the sum of the Index 1 section of OverrideCycles.",
                },
                "Index2Cycles": {
                    "type": "integer",
                    "minimum": 1,
                    "description": "Number of cycles in the first Index Read. Required when sequencing more than one sample. If OverrideCycles is present in the [BCLConvert_Settings] section, this value must be consistent with the sum of the Index 2 section of OverrideCycles.",
                },
            },
        },
        "Sequencing_Settings": {
            "type": "object",
            "required": [],
            "properties": {
                "LibraryPrepKits": {
                    "type": "string",
                    "description": "Your library prep kit. Only one library prep kit is allowed.",
                }
            },
        },
        "BCLConvert_Settings": {
            "type": "object",
            "required": ["SoftwareVersion"],
            "properties": {
                "AdapterRead1": {
                    "type": "string",
                    "pattern": r"^[ACGT]+",
                    "description": "The sequence to trim or mask from the end of Read 1. AdapterRead1 trims cycles by default. Value must be <= Read1Cycles.",
                },
                "AdapterRead2": {
                    "type": "string",
                    "pattern": r"^[ACGT]+",
                    "description": "The sequence to trim or mask from the end of Read 2. AdapterRead2 trims cycles by default. Value must be <= Read2Cycles.",
                },
                "BarcodeMismatchesIndex1": {
                    "type": "integer",
                    "minimum": 0,
                    "maximum": 2,
                    "default": 1,
                    "description": "The number of allowed mismatches between the first Index Read and index sequence. Only required if Index1Cycles is specified.",
                },
                "BarcodeMismatchesIndex2": {
                    "type": "integer",
                    "minimum": 0,
                    "maximum": 2,
                    "default": 1,
                    "description": "The number of allowed mismatches between the first Index Read and index sequence. Only required if Index2Cycles is specified.",
                },
                "FastqCompressionFormat": {
                    "type": "string",
                    "enum": ["dragen", "gzip"],
                },
                "OverrideCycles": {
                    "type": "string",
                    "pattern": r"^([NYIU][0-9]+;?){1,}$",
                },
                "SoftwareVersion": {
                    "type": "string",
                    "pattern": r"^[0-9]+\.[0-9]+.*",
                },
            },
            "BCLConvert_Data": {
                "type": "object",
                "required": ["Sample_ID"],
                "properties": {
                    "Sample_ID": {
                        "type": "string",
                        "pattern": r"^[a-zA-Z0-9\-_]+$",
                        "maxLength": 20,
                        "description": "The ID of the sample. Separate each identifier with a dash or underscore.",
                        "examples": ["Sample1-DQB1-022515"],
                    },
                    "Index": {
                        "type": "string",
                        "pattern": r"^[ACTG]+$",
                        "description": "The index sequence associated with the sample. Required when sequencing more than one sample.",
                    },
                    "Index2": {
                        "type": "string",
                        "pattern": r"^[ACTG]+$",
                        "description": "The second index sequence associated with the sample. Make sure the second index (i5) adapter sequences are in forward orientation. DRAGEN automatically reverse complements i5 indexes during secondary analysis.",
                    },
                    "Lane": {
                        "type": "integer",
                        "minimum": 0,
                        "description": "The lane of the flow cell. Lanes are represented by one integer value.",
                    },
                    "Sample_Project": {
                        "type": "string",
                        "pattern": r"^[a-zA-Z0-9\-_]+$",
                        "maxLength": 20,
                    },
                },
            },
        },
    },
}
registry = Resource.from_contents(illuminasamplesheetv2schema) @ registry


def parse_overrideCycles(cyclestr: str) -> dict[str, str]:
    """validates and expands strings typically found in OverrideCycles into a dict with keys that correspond to the respective entry,
    For example Y53;I8;N8U16;Y53 will be parsed into
    ```
    {
      'Read1Cycles': 'YYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYY',
      'Index1Cycles': 'IIIIIIII',
      'Index2Cycles': 'NNNNNNNNUUUUUUUUUUUUUUUU',
      'Read2Cycles': 'YYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYY'
    }
    ```
    This structure is easily processable, e.g. to get the total cycle length
    ```
    sum([len(v) for v in parse_overrideCycles("Y53;I8;N8U16;Y53").values()])
    ```
    or to compare lengths with the corresponding Reads entries:
    ```
    ovrCycles = parse_overrideCycles("Y53;I8;N8U16;Y53")
    all([len(ovrCycles[k]) == v for k,v in secsheet['Reads'].items()])
    ```
    """

    def expand(short: str) -> str:
        res = ""
        pt = re.compile("([NYIU]+)([0-9]*);?")
        matches = re.findall(pt, short)
        for letter, freq in matches:
            res += letter * int(freq)
        return res

    def is_read_or_umi(s: str) -> bool:
        return ("Y" in s) or ("U" in s)

    cycles = cyclestr.split(";")
    if len(cycles) < 1:
        raise Exception(
            f"OverrideCycles {cyclestr} cannot be parsed to a cycle sequence."
        )
    res = {"Read1Cycles": expand(cycles[0])}
    if len(cycles) == 2:
        # cycles[1] may now either be the second read, or the first index
        cyc = expand(cycles[1])
        if is_read_or_umi(cyc):
            res["Read2Cycles"] = cyc
        else:
            res["Index1Cycles"] = cyc
    elif len(cycles) == 3:
        res["Index1Cycles"] = expand(cycles[1])
        # there may be two indices but just one read
        if "Y" in cycles[2]:
            res["Read2Cycles"] = expand(cycles[2])
        elif "I" in cycles[2] or "N" in cycles[2] or "U" in cycles[2]:
            res["Index2Cycles"] = expand(cycles[2])
        else:
            # there may be edge cases. If these occur, then probably one needs to resort to the sequencing settings section.
            raise Exception(
                "cannot determine type of third element in OverrideCycles. Probably an implementation error."
            )
    elif len(cycles) == 4:
        res["Index1Cycles"] = expand(cycles[1])
        res["Index2Cycles"] = expand(cycles[2])
        res["Read2Cycles"] = expand(cycles[3])
    elif len(cycles) == 1:
        pass
    else:
        raise Exception(f"OverrideCycles {cyclestr} defines too many elements.")
    if not is_read_or_umi(res["Read1Cycles"]):
        raise Exception(
            f"Read1Cycles entry in OverrideCycles is not a read: {res['Read1Cycles']}"
        )
    if ("Read2Cycles" in res) and (not is_read_or_umi(res["Read2Cycles"])):
        raise Exception(
            f"Read2Cycles entry in OverrideCycles is not a read: {res['Read2Cycles']}"
        )
    if ("Index1Cycles" in res) and (is_read_or_umi(res["Index1Cycles"])):
        raise Exception(
            f"Index1Cycles entry in OverrideCycles contains reads: {res['Index1Cycles']}"
        )
    if ("Index2Cycles" in res) and (is_read_or_umi(res["Index2Cycles"])):
        raise Exception(
            f"Index2Cycles entry in OverrideCycles contains reads: {res['Index2Cycles']}"
        )
    return res


def illuminasamplesheetv2logic(doc: SectionedSheet) -> None:
    """
    this function checks the logic that is described in
    https://support-docs.illumina.com/IN/NextSeq10002000/Content/SHARE/SampleSheetv2/SampleSheetValidation_fNS_m2000_m1000.htm

    We won't check at the level of the index kits (i.e. that the indices match the kit etc)
    """
    cycles: dict[str, str] = {}
    if "BCLConvert_Settings" in doc:
        convertsettings = cast(Settings, doc["BCLConvert_Settings"])
        readsettings = cast(Settings, doc["Reads"])
        if "OverrideCycles" in convertsettings:
            cycles = parse_overrideCycles(str(convertsettings["OverrideCycles"]))
            for elemname, elemseq in cycles.items():
                if elemname not in doc["Reads"]:
                    raise Exception(
                        f"BCLConvert_Settings.OverrideCycles defines {elemname}, but it is not specified in the Reads section"
                    )
                if int(readsettings[elemname]) != len(elemseq):
                    raise Exception(
                        f"Reads.{elemname} is {readsettings[elemname]}, but BCLConvert_Settings.OverrideCycles specifies a length of {len(elemseq)}"
                    )
            for elemname in [
                i
                for i in ["Read1Cycles", "Read2Cycles", "Index1Cycles", "Index2Cycles"]
                if i in readsettings.keys()
            ]:
                if elemname not in cycles.keys():
                    raise Exception(
                        f"Reads defines {elemname}, but BCLConvert_Settings.OverrideCycles {convertsettings['OverrideCycles']} is incompatible with it."
                    )
        else:
            # generate dummy overrideCycles structure
            cycles = {
                k: "Y" * cast(int, v) if k.startswith("Read") else "I" * cast(int, v)
                for k, v in readsettings.items()
            }

        if "AdapterRead1" in doc["BCLConvert_Settings"]:
            if len(cast(str, convertsettings["AdapterRead1"])) > cast(
                int, readsettings["Read1Cycles"]
            ):
                raise Exception(
                    f"BCLConvert_Settings.AdapterRead1 is longer then Reads.Read1Cycles"
                )
        if "AdapterRead2" in doc["BCLConvert_Settings"]:
            if "Read2Cycles" not in doc["Reads"]:
                raise Exception(
                    "AdapterRead2 defined in BCLConvert_Settings, but no Read2Cycles entry in Reads"
                )
            if len(cast(str, convertsettings["AdapterRead2"])) > cast(
                int, readsettings["Read2Cycles"]
            ):
                raise Exception(
                    "BCLConvert_Settings.AdapterRead2 is longer then Reads.Read2Cycles"
                )
        # The "spec" also says:
        # "BarcodeMismatchesIndex[12]: Only required if Index[12]Cycles is specified."
        # but this conflicts with a default value of 1.
    if "BCLConvert_Data" in doc:
        # Sample_ID do not need to be unique?!
        convertdata = cast(Data, doc["BCLConvert_Data"])
        if len(convertdata) > 1:
            if not all(["Index" in sample for sample in convertdata]):
                raise Exception(
                    "No Index found in BCLConvert_Data, although it contains more than one sample"
                )
            index1 = [i["Index"] for i in convertdata]
            minindex1length = cycles["Index1Cycles"].count("I")
            maxindex1length = len(cycles["Index1Cycles"])
            if not all(
                [
                    (len(index) >= minindex1length and len(index) <= maxindex1length)
                    for index in index1
                ]
            ):
                raise Exception(
                    f"(At least some) First indices of the samples have a different length than what is specified in OverrideCycles ({minindex1length})"
                )

            if "Index2" in convertdata[0]:
                index2 = [i["Index2"] for i in convertdata]
                index = [i1 + i2 for i1, i2 in zip(index1, index2)]
                minindex2length = cycles["Index2Cycles"].count("I")
                maxindex2length = len(cycles["Index2Cycles"])
                if not all(
                    [
                        (
                            len(index) >= minindex2length
                            and len(index) <= maxindex2length
                        )
                        for index in index2
                    ]
                ):
                    raise Exception(
                        f"(At least some) Second indices of the samples have a different length than what is specified in OverrideCycles ({minindex2length})"
                    )
            else:
                index = index1

            # indices may be equal if on separate lanes, so we add the lane as an additional identifier prefix:
            if "Lane" in convertdata[0]:
                lane = [i["Lane"] for i in convertdata]
                index = [str(l) + i for l, i in zip(lane, index)]

            # finally, check if there are non-unique indices:
            if len(set(index)) != len(index):
                raise Exception("Indices are not unique.")


def basespacelogic(doc: SectionedSheet) -> None:
    if "Cloud_Data" not in doc:
        raise Exception("no Cloud_Data section")
    if "BCLConvert_Data" not in doc:
        raise Exception("no BCLConvert_Data section")
    cloud_sample_ids = [i["Sample_ID"] for i in cast(Data, doc["Cloud_Data"])]
    bclconvert_sample_ids = [i["Sample_ID"] for i in cast(Data, doc["BCLConvert_Data"])]
    for convert_id in bclconvert_sample_ids:
        if convert_id not in cloud_sample_ids:
            raise Exception(
                f"Sample_ID {convert_id} is defined in the BCLConvert_Data section, but not in the Cloud_Data section."
            )
    # TODO should we test also for the reverse? I.e. is it allowed that there are samples defined in Cloud_Data that are not in BCLConvert_Data
    # currently we allow for that.
    cloudsamples = {x["Sample_ID"]: x for x in cast(Data, doc["Cloud_Data"])}
    convertsamples = {x["Sample_ID"]: x for x in cast(Data, doc["BCLConvert_Data"])}
    commonkeys = list(set(cloudsamples.keys()).intersection(set(convertsamples)))
    for sampleid in commonkeys:
        for index in ["Index", "Index2"]:
            if index in cloudsamples[sampleid] and index in convertsamples[sampleid]:
                if cloudsamples[sampleid][index] != convertsamples[sampleid][index]:
                    raise Exception(
                        f"Index of {sampleid} does not match between Cloud_Data ({cloudsamples[sampleid][index]}) and BCLConvert_Data ({convertsamples[sampleid][index]}) "
                    )


def check_index_distance(doc: SectionedSheet, mindist: Optional[int] = None) -> None:
    """checks the pairwise distance (Hamming distance) between indices to be smaller than or equal to the values
    specified by BarcodeMismatchIndex[12] (they default to 1 in illumina sample sheets).
    If mindist is given, an additional check on the combined index (index1 + index2) is performed: This combined index is required to have a pairwise distance of at most mindist.
    """

    if mindist is not None and mindist < 1:
        raise ValueError("minimal index distance must be >= 1.")

    def pairwise_index_distance(a: str, b: str) -> int:
        """returns the number of unequal digits (Hamming distance) between the two sequences.
        if the two sequences have different lengths, only the left-most digits are compared.
        """
        shorter = a if len(a) < len(b) else b
        longer = a if len(a) >= len(b) else b
        if len(shorter) < len(longer):
            # fill the remaining space with the longer sequence so that it does not add to the distance
            shorter = shorter + longer[-(len(longer) - len(shorter)) :]
        return sum([shorter[i] != longer[i] for i in range(len(shorter))])

    def index_distances(
        indices: list[list[str]],
    ) -> list[Tuple[list[int], list[str], list[str]]]:
        """returns the pairs of indices and their Hammon distances.
        Indices is an array to account for multiple indices.
        For every pair, the array of distances (one for each index) and the two indices compared are returned
        """
        if len(indices) == 1:
            # if there is only one index entry, we return the one entry and the length of the indices
            return [([len(i) for i in indices[0]], indices[0], indices[0])]
        elif len(indices) == 0:
            raise Exception("no indices.")

        return [
            (
                [
                    pairwise_index_distance(comb[0][i], comb[1][i])
                    for i in range(len(comb[0]))
                ],
                comb[0],
                comb[1],
            )
            for comb in itertools.combinations(indices, 2)
        ]

    def check_index(
        doc: SectionedSheet,
        indexnames: list[str] | str,
        mismatchnames: list[str] | str,
        mindist: Optional[int] = None,
    ):
        if isinstance(indexnames, str):
            indexnames = [indexnames]
        if isinstance(mismatchnames, str):
            mismatchnames = [mismatchnames]
        lanes = set(
            [
                int(i["Lane"]) if "Lane" in i else 1
                for i in cast(Data, doc["BCLConvert_Data"])
            ]
        )
        for lane in lanes:
            this_lane_data = [
                i
                for i in cast(Data, doc["BCLConvert_Data"])
                if ("Lane" in i and int(i["Lane"]) == lane) or ("Lane" not in i)
            ]

            index = [
                [
                    i[indexname] if indexname in i and i[indexname] is not None else ""
                    for indexname in indexnames
                ]
                for i in this_lane_data
            ]

            mismatches = [
                cast(int, cast(Settings, doc["BCLConvert_Settings"])[mismatchname])
                if mismatchname in doc["BCLConvert_Settings"]
                else 1
                for mismatchname in mismatchnames
            ]

            indexdist = index_distances(index)
            matchingindices = [
                t
                for t in indexdist
                if all([t[0][i] <= mismatches[i] for i in range(len(mismatches))])
            ]
            if len(matchingindices) > 0:
                msg = "Indices are too close and undistinguishable: "
                for matchingindex in matchingindices:
                    msg += f"Entries of index pair ({str(matchingindex[1])}, {str(matchingindex[2])}) are undistinguishable because "
                    for i, indexname in enumerate(indexnames):
                        if matchingindex[0][i] <= mismatches[i]:
                            msg += f"{indexname} differs by {matchingindex[0][i]} <= {mismatches[i]} "
                    msg += ". "
                raise Exception(msg)

            if mindist is not None:
                combined = [["".join(i)] for i in index]
                indexdist = index_distances(combined)
                matchingindices = [t for t in indexdist if all([t[0][0] < mindist])]
                if len(matchingindices) > 0:
                    msg = "Combined index is too close and undistinguishable: "
                    for matchingindex in matchingindices:
                        msg += f"Entries of index pair ({str(matchingindex[1])}, {str(matchingindex[2])}) are undistinguishable because their distance is {matchingindex[0][0]} < {mindist} (which is the explicitly given combined minimal distance)"
                    raise Exception(msg)

    convdata = cast(Data, doc["BCLConvert_Data"])
    if "Index" in convdata[0] and "Index2" in convdata[0]:
        check_index(
            doc,
            ["Index", "Index2"],
            ["BarcodeMismatchesIndex1", "BarcodeMismatchesIndex2"],
            mindist,
        )

    elif "Index" in convdata[0]:
        check_index(doc, "Index", "BarcodeMismatchesIndex1", mindist)
    elif "Index2" in convdata[0]:
        check_index(doc, "Index2", "BarcodeMismatchesIndex2", mindist)


# this is implemented according to https://support-docs.illumina.com/IN/NextSeq10002000/Content/SHARE/SampleSheetv2/SampleSheetValidation_fNS_m2000_m1000.htm
# but seems to be false (there are UMIs that are longer than 10)
# after a call with illumina support it turns out indices must not be longer than 10 cycles,
# but UMIs may be.
# UMIs should always be in Index2.
# So Index1 must be longer than 10 and Index2 must ONLY be longer than 10 if it contains the UMIs.
# Basespace in that case sets OverrideCycles accordingly
#
nextseq1k2kschema = {
    "$id": "urn:samshee:illuminav2-nextseq/v1",
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "required": ["Header", "Reads"],
    "properties": {
        "Reads": {
            "type": "object",
            "properties": {
                "Index1Cycles": {"maximum": 10},
                "Index2Cycles": {"maximum": 24},
            },
        }
    },
}
registry = Resource.from_contents(nextseq1k2kschema) @ registry


def nextseq1k2klogic(doc: SectionedSheet) -> None:
    if "BCLConvert_Settings" in doc:
        if "OverrideCycles" in doc["BCLConvert_Settings"]:
            cycles = parse_overrideCycles(
                str(cast(Settings, doc["BCLConvert_Settings"])["OverrideCycles"])
            )
            if "U" in cycles["Index1Cycles"]:
                raise Exception("Index1 typically does not contain UMIs")
            if (
                ("Index2Cycles" in cycles)
                and (len(cycles["Index2Cycles"]) > 10)
                and (not "U" in cycles["Index2Cycles"])
            ):
                raise Exception(
                    "Reads.Index2 must have a maximum length of 10 if it contains only an index and no UMIs."
                )


def validate(
    doc: SectionedSheet,
    validation: Callable | dict | list[Callable | dict],
    registry=registry,
) -> None:
    """validation may either be a callable function or a dict specifying a (in-built or retrievable) json schema, e.g. {"$ref": "urn:samshee:illuminav2/v1"}"""
    # TODO validation may also contain schema URLs
    if validation is None:
        schemata = []
    elif isinstance(validation, list):
        pass
    else:
        validation = [
            validation
        ]  # if there is only one entry, we allow to pass it not as a list
    for i, schema in enumerate(validation):
        if not (isinstance(schema, dict) or callable(schema)):
            if hasattr(schema, "name"):
                raise Exception(
                    f"validator / schema {schema.name} (#{i}) is not a schema or is not callable."
                )
            else:
                raise Exception(
                    f"anonymous validator / schema #{i} is not a schema or is not callable."
                )

    for i, schema in enumerate(validation):
        if isinstance(schema, dict):
            name = f"validator #{i} ({schema})"
            v = Draft202012Validator(schema, registry=registry).iter_errors(doc)
            errs = []
            for err in v:
                errs.append((err.json_path, err.message))
            if len(errs) == 1:
                raise Exception(
                    f"{name} raised validation error: {errs[0][0]}: {errs[0][1]}"
                )
            elif len(errs) > 1:
                msg = "\n".join(["- " + e[0] + ": " + e[1] for e in errs])
                raise Exception(f"{name} raised validation errors:\n{msg}")
        elif callable(schema):
            name = f"anonymous validation function #{i}"
            try:
                schema(doc)
            except Exception as exc:
                raise Exception(f"{name} raised validation error: {exc}")
        else:
            raise Exception(
                f"anonymous validator / schema #{i} is not a schema or is not callable."
            )
