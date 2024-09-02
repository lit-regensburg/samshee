#!/usr/bin/env python3
from samshee.samplesheetv2 import read_samplesheetv2, parse_samplesheetv2_from_json
#from samshee.samplesheetv1 import read_samplesheetv1
from samshee.sectionedsheet import read_sectionedsheet
import sys
import argparse
from pathlib import Path

parser = argparse.ArgumentParser()

parser.add_argument(
    "infile",
    help="input sample sheet",
)
parser.add_argument("--output-format", help="print the read sheet in this format (possible values: v1, v2, sectioned, json)", default="v2")
parser.add_argument("--input-format", help="expect the input file to be in this format (possible values: v2, json)", default="v2")

args = parser.parse_args()

infile = Path(args.infile)

if args.input_format == "json":
    with infile.open("r") as fh:
        jstr = fh.read()
    sheet = parse_samplesheetv2_from_json(jstr)
elif args.input_format == "v2":
    sheet = read_samplesheetv2(infile)
elif args.input_format == "sectioned":
    sheet = read_sectionedsheet(infile)
#elif args.input_format == "v1":
#    sheet = read_samplesheetv1(infile)
else:
    raise ValueError(f"Unknown input format: {args.input_format}")

if args.output_format == "json":
    print(sheet.to_json(pretty=True))
elif args.output_format == "v2":
    print(sheet)
else:
    raise ValueError(f"Unknown output format: {args.output_format}")
