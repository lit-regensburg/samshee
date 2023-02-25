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


def test_if_mindist_is_used_if_given_explicitly():
    # the two sequences below ACAA and ACTT have a distance of two
    # BarcodeMismatches1 = 1 by default, so this should check (and demultiplex) fine, because if there is one read error, the two are still distinguishable
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
        )
    )
    # However, now we set mindist = 3 explicitly, meaning the barcodes should be different in at least three positions
    # (equivalently in this case, we could have set barcodemismatches = 2. If we had two indices, mindist would apply to the combined)
    # therefore, the following should now raise an exception, because it violates the mindist requirement (but not the BarcodeMismatches Requirement)
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
    # setting mindist = 2 should be fine again:
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
        mindist=2,
    )


def test_if_check_index_distance_accepts_two_indices_with_different_mismatches():
    # below is okay, because the first index has a dist of one, which is sufficient with mismatches=0.
    # the other index is constant, so only the first index differentiates the samples.
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
                    {"Sample_ID": "b", "Index": "TTTA", "Index2": "ACAA"},
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
                        {"Sample_ID": "b", "Index": "TTTA", "Index2": "ACAA"},
                    ],
                }
            )
        )
    # equally, if we set mindist = 2, this should fail:
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
                        {"Sample_ID": "b", "Index": "TTTA", "Index2": "ACAA"},
                    ],
                }
            ),
            mindist=2,
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


def test_if_check_index_distance_accepts_two_indices_that_are_different():
    with pytest.raises(Exception):
        check_index_distance(
            SectionedSheet(
                {
                    "Reads": {},
                    "BCLConvert_Settings": {},
                    "BCLConvert_Data": [
                        {"Sample_ID": "a", "Index": "TTTT", "Index2": "ACAA"},
                        {"Sample_ID": "b", "Index": "TTTA", "Index2": "ACAA"},
                        {"Sample_ID": "b", "Index": "TTTT", "Index2": "ACAC"},
                        {"Sample_ID": "b", "Index": "TTTA", "Index2": "ACAC"},
                    ],
                }
            ),
            mindist=1,  # index2 has mindist of 2, which should be okay.
        )
