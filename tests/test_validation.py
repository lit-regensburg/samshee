#!/usr/bin/env python3
import pytest
from samshee.validation import check_index_distance
from samshee.sectionedsheet import SectionedSheet


def test_if_check_index_distance_accepts_only_mindists_larger_than_0():
    with pytest.raises(ValueError):
        check_index_distance(
            SectionedSheet(
                {
                    "Reads": {},
                    "BCLConvert_Settings": {},
                    "BCLConvert_Data": [
                        {"Sample_ID": "a", "Index": "ACA"},
                        {"Sample_ID": "b", "Index": "ACC"},
                    ],
                }
            ),
            mindist=0,
        )


def test_if_check_index_distance_uses_BarcodeMismatches_rather_than_mindist():
    # no barcode mismatches, mindist is used and should raise here, because distance
    # of ACAA to ACTT is 2 and 3 is required
    with pytest.raises(Exception):
        check_index_distance(
            SectionedSheet(
                {
                    "Reads": {},
                    "BCLConvert_Settings": {},
                    "BCLConvert_Data": [
                        {"Sample_ID": "a", "Index": "ACAA"},
                        {"Sample_ID": "b", "Index": "ACTT"},
                    ],
                }
            ),
            mindist=3,
        )
    # but here, there is barcodemismatches=1 in the sheet.
    # meaning: one mismatch is allowed for two indices to be considered equal.
    # Hence, ACAA and ACTT are different enough and should not fail
    check_index_distance(
        SectionedSheet(
            {
                "Reads": {},
                "BCLConvert_Settings": {"BarcodeMismatchesIndex1": 1},
                "BCLConvert_Data": [
                    {"Sample_ID": "a", "Index": "ACAA"},
                    {"Sample_ID": "b", "Index": "ACTT"},
                ],
            }
        ),
        mindist=3,
    )


def test_if_check_index_distance_accepts_two_indices_with_different_mismatches():
    # below is okay, because the first index has a dist of one, which is sufficient with mismatches=0.
    # the second has a dist of two, which is sufficient with mismatches=1
    check_index_distance(
        SectionedSheet(
            {
                "Reads": {},
                "BCLConvert_Settings": {
                    "BarcodeMismatchesIndex1": 0,
                    "BarcodeMismatchesIndex2": 1,
                },
                "BCLConvert_Data": [
                    {"Sample_ID": "a", "Index": "TTTT", "Index2": "ACAA"},
                    {"Sample_ID": "b", "Index": "TTTA", "Index2": "ACTT"},
                ],
            }
        )
    )
    # if we set the first to one, this should reject:
    with pytest.raises(Exception):
        check_index_distance(
            SectionedSheet(
                {
                    "Reads": {},
                    "BCLConvert_Settings": {
                        "BarcodeMismatchesIndex1": 1,
                        "BarcodeMismatchesIndex2": 1,
                    },
                    "BCLConvert_Data": [
                        {"Sample_ID": "a", "Index": "TTTT", "Index2": "ACAA"},
                        {"Sample_ID": "b", "Index": "TTTA", "Index2": "ACTT"},
                    ],
                }
            )
        )


def test_if_check_index_distance_accepts_two_indices_with_one_uniform():
    # this requires the index distance of all non-uniform indices (index2 in this case) to be at least 2.
    check_index_distance(
        SectionedSheet(
            {
                "Reads": {},
                "BCLConvert_Settings": {},
                "BCLConvert_Data": [
                    {"Sample_ID": "a", "Index": "TTTT", "Index2": "ACAA"},
                    {"Sample_ID": "b", "Index": "TTTT", "Index2": "ACTT"},
                ],
            }
        ),
        mindist=2,  # index2 has mindist of 2, which should be okay.
    )


def test_if_check_index_distance_rejects_two_indices_with_two_uniform():
    with pytest.raises(Exception):
        check_index_distance(
            SectionedSheet(
                {
                    "Reads": {},
                    "BCLConvert_Settings": {},
                    "BCLConvert_Data": [
                        {"Sample_ID": "a", "Index": "TTTT", "Index2": "ACAA"},
                        {"Sample_ID": "b", "Index": "TTTT", "Index2": "ACAA"},
                    ],
                }
            ),
            mindist=2,  # index2 has mindist of 2, which should be okay.
        )
