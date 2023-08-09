#!/usr/bin/env python3
from samshee.samplesheetv2 import read_samplesheetv2
import sys

infile = sys.argv[1]
print(read_samplesheetv2(infile))
