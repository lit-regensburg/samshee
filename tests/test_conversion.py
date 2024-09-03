#!/usr/bin/env python3
import pytest
from samshee.sectionedsheet import SectionedSheet, read_sectionedsheet, parse_array, parse_sectionedsheet_from_json
import tempfile
from io import StringIO
from pathlib import Path


def test_can_convert_to_json_and_back():
    fh = StringIO(
        """
[Header],
FileFormatVersion,2
RunName,p123_A_scGEX_scCSP_Novaseq
InstrumentPlatform,NovaSeq
IndexOrientation,Forward

[Reads]
Read1Cycles,28
Read2Cycles,90
Index1Cycles,10
Index2Cycles,10

[BCLConvert_Data]
Lane,Sample_ID,Index,Index2
1,scGEX_A2,GTGGATCAAA,GCCAACCCTG
2,scGEX_A2,GTGGATCAAA,GCCAACCCTG
3,scGEX_A2,GTGGATCAAA,GCCAACCCTG
4,scGEX_A2,GTGGATCAAA,GCCAACCCTG
"""
    )
    sheet = read_sectionedsheet(fh)
    sheet_from_json = parse_sectionedsheet_from_json(sheet.to_json())
    assert str(sheet) == str(sheet_from_json)
