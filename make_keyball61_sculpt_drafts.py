#!/usr/bin/env python3
"""
Create left/right Keyball61 Sculpt-keycap draft files from Ergohaven's
upstream Sculpt_keycaps_v1.py.

Usage:
    1. Put this file in the same folder as Sculpt_keycaps_v1.py
    2. Run:
           python make_keyball61_sculpt_drafts.py
    3. It creates:
           Sculpt_keycaps_keyball61_left_draft.py
           Sculpt_keycaps_keyball61_right_draft.py

Draft assumptions
-----------------
The existing Ergohaven 7-column matrix is treated as:

    col 0   col 1   col 2   col 3   col 4   col 5   col 6
    pinky   pinky   ring    middle  index   index   special/unused

This is an ASSUMPTION and should be checked against the generated preview
before printing a full set.

The upstream row/column sweep angles and face tilts are deliberately kept
unchanged for this first ergonomic draft.  Only explicit key heights are
modified.  This gives a much cleaner A/B test of the finger-length
compensation before tuning yaw/pitch further.
"""

from pathlib import Path
import re
import sys

SRC = Path("Sculpt_keycaps_v1.py")

# Current upstream explicit heights (2026-09-07), used as the geometric
# baseline.  The offsets below are added per finger column.
BASE_HEIGHTS = [
    [13.0, 11.0,  9.0,  9.0, 11.0, 13.0,  0.0],
    [10.4,  7.9,  5.9,  5.7,  7.9, 10.4,  0.0],
    [ 9.8,  7.3,  5.0,  5.0,  6.8,  9.3,  0.0],
    [12.0, 10.0,  8.0,  8.0,  9.5, 11.8, 13.8],
    [ 0.0,  0.0, 11.0, 11.0,  0.0,  0.0,  0.0],
]

# Suggested FIRST TEST offsets, in mm.
#
# Left measurements:
# pinky 66.5, ring 84.5, middle 90.0, index 91.5
#
# Right measurements:
# pinky 66.0, ring 82.0, middle 89.0, index 82.0
#
# These are deliberately much smaller than the raw finger-length
# differences.  They are ergonomic trial values, not a 1:1 conversion.
LEFT_COLUMN_OFFSETS  = [5.0, 5.0, 2.0, 0.0, 0.0, 0.0, 0.0]
RIGHT_COLUMN_OFFSETS = [5.0, 5.0, 2.5, 0.0, 2.5, 2.5, 0.0]


def adjusted_heights(offsets):
    out = []
    for r, row in enumerate(BASE_HEIGHTS):
        new_row = []
        for c, h in enumerate(row):
            # Keep zero-height/non-key placeholders untouched.
            if h == 0.0:
                new_row.append(0.0)
            else:
                new_row.append(round(h + offsets[c], 2))
        out.append(new_row)
    return out


def matrix_to_python(name, matrix, hand):
    lines = [
        f"# --- Keyball61 {hand} hand draft: finger-length compensation ---",
        "# [Inference] Trial geometry based on measured finger lengths.",
        "# Verify column mapping in CQ-Editor before printing the whole set.",
        f"{name}: List[List[Optional[float]]] = [",
    ]
    labels = [
        "row 0",
        "row 1",
        "row 2 / home-ish",
        "row 3",
        "row 4 / special",
    ]
    for label, row in zip(labels, matrix):
        vals = ", ".join(f"{x:.2f}" for x in row)
        lines.append(f"    [{vals}],  # {label}")
    lines.append("]")
    return "\n".join(lines)


def patch_one(src_text, hand, offsets):
    heights = adjusted_heights(offsets)
    new_height_block = matrix_to_python("KEY_HEIGHT", heights, hand)

    # Replace only the explicit KEY_HEIGHT matrix; keep Ergohaven's
    # KEY_ANGLES and KEY_FACE_TILT untouched for the first test.
    pattern = re.compile(
        r"# Explicit per-key heights in mm\. Use None to keep sweep-derived height\.\s*"
        r"KEY_HEIGHT:\s*List\[List\[Optional\[float\]\]\]\s*=\s*\[.*?\n\s*\]",
        flags=re.S,
    )

    replacement = (
        "# Explicit per-key heights in mm. Use None to keep sweep-derived height.\n"
        + new_height_block
    )

    patched, count = pattern.subn(replacement, src_text, count=1)
    if count != 1:
        raise RuntimeError(
            "Could not locate KEY_HEIGHT in Sculpt_keycaps_v1.py. "
            "The upstream file may have changed."
        )

    # One file per hand is intentional because the upstream script has one
    # global KEY_HEIGHT matrix shared by the selected mode.
    patched = re.sub(
        r'(?m)^MODE\s*=\s*["\'](?:single|left|right|both)["\']\s*$',
        f'MODE = "{hand}"',
        patched,
        count=1,
    )

    # Draft quality is much faster while checking geometry.
    patched = re.sub(
        r'(?m)^QUALITY\s*=\s*["\'](?:draft|production)["\']\s*$',
        'QUALITY = "draft"',
        patched,
        count=1,
    )

    banner = f