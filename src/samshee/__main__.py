#!/usr/bin/env python3
from samshee.samplesheetv2 import SampleSheetV2, read_samplesheetv2, parse_samplesheetv2_from_json
from samshee.sectionedsheet import read_sectionedsheet
from samshee.validation import validate
import sys
import argparse
import json
from pathlib import Path

parser = argparse.ArgumentParser()

parser.add_argument(
    "infile",
    help="input sample sheet. Use \"-\" for stdin.",
)
parser.add_argument("--input-format", help="expect the input file to be in this format (possible values: sectioned, json) (v1 sheets can be read as sectioned sheets but are not validated by default!)", default="sectioned")
parser.add_argument("--output-format", help="print the read sheet in this format (possible values: sectioned, v2, json).", default="v2")
parser.add_argument("--schema", help="specifies an additional schema (other than those required by the input or output formats) in json format, e.g. \'{\"required\": [\"Header\", \"Reads\"]}\'. Use \"$ref\" for linking to predefined external or samshee-internal schemas, e.g., \'{\"$ref\": \"urn:samshee:illuminav2/v1\"}\'. This argument can be given more than once.", default=[], action="append", type=str)

args = parser.parse_args()

if args.infile == "-":
    infile = sys.stdin
else:
    infile = Path(args.infile)

try:
    if args.input_format == "json":
        with infile.open("r") as fh:
            jstr = fh.read()
        sheet = parse_samplesheetv2_from_json(jstr)
    elif args.input_format == "sectioned":
        sheet = read_sectionedsheet(infile)
    else:
        print(f"Unknown input format: {args.input_format}. Must be json or sectioned. Use \"sectioned\" for any v1 or v2 sample sheets.", file=sys.stderr)
        sys.exit(3)
except Exception as exc:
    print(f"Error reading sheet: {exc}", file=sys.stderr)
    sys.exit(1)

try:
    validate(sheet, validation=[json.loads(schema) for schema in args.schema])
except Exception as exc:
    print(f"Validation failed: {exc}", file=sys.stderr)
    sys.exit(2)


try:
    if args.output_format == "json":
        print(sheet.to_json(pretty=True))
    elif args.output_format == "v2":
        print(SampleSheetV2(sheet))
    elif args.output_format == "sectioned":
        print(sheet)
    else:
        print(f"Unknown output format: {args.output_format}. Must be json, v2, or sectioned.", file=sys.stderr)
        sys.exit(3)
except Exception as exc:
    print(f"failed writing output: {exc}", file=sys.stderr)
    sys.exit(4)
