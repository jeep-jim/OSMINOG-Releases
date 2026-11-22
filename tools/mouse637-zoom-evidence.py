#!/usr/bin/env python3
"""Bind retained zoom pixels to the explicitly requested637 sidebar dim.

Only the four settings guest captures use the black14% composite. The exact
capture name is already bound to its zoom scenario by the retained validator;
its report cannot choose another palette. Frozen633–636 files, RGB tolerance,
meter geometry/density, raw PNG decoding and native ownership stay unchanged.
"""
import math
import re

ORIGINAL = (235, 40, 155)
OPACITY = .14
DIMMED = tuple(math.floor(value * (1 - OPACITY) + .5) for value in ORIGINAL)


def expected_rgb(row):
    name = row.get('filename') if isinstance(row, dict) else None
    match = re.fullmatch(r'mouse-633-zoom-(popover|settings)-(before|after)-guest-[01]\.png', name or '')
    if match is None:
        raise ValueError('Mouse637 zoom presentation lacks an exact bound guest frame')
    kind = match.group(1)
    dimmed = kind == 'settings'
    rgb = DIMMED if dimmed else ORIGINAL
    presentation = row.get('presentation')
    if (not isinstance(presentation, dict) or type(presentation.get('dimmed')) is not bool
            or type(presentation.get('expectedRGB')) is not list
            or any(type(channel) is not int for channel in presentation['expectedRGB'])
            or presentation != {'kind': kind, 'dimmed': dimmed, 'expectedRGB': list(rgb)}):
        raise ValueError('Mouse637 zoom presentation differs from its required sidebar state')
    return rgb
