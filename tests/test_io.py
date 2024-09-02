#!/usr/bin/env python3
import pytest
from samshee.sectionedsheet import SectionedSheet, read_sectionedsheet, parse_array
import tempfile
from io import StringIO
from pathlib import Path


def test_can_read_from_open_file():
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
"""
    )
    read_sectionedsheet(fh)


def test_can_read_from_path():
    tempdir = tempfile.TemporaryDirectory()
    fname = Path(tempdir.name) / "sheet.csv"
    with fname.open("w") as fh:
        fh.write(
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
"""
        )

    read_sectionedsheet(fname)


def test_can_read_binary_from_path():
    tempdir = tempfile.TemporaryDirectory()
    fname = Path(tempdir.name) / "sheet.csv"
    with fname.open("w") as fh:
        fh.write(
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
"""
        )

    with fname.open("rb") as fh:
        read_sectionedsheet(fh)

def test_can_read_array():
    s = """
[Reads]
28,
90,
10,,
10
"""
    a = parse_array(s)
    assert len(a) == 4
    assert a[0] == 28
    assert a[1] == 90
    assert a[2] == 10
    assert a[3] == 10
