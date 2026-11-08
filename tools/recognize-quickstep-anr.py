#!/usr/bin/env python3
"""Recognize only the observed AOSP launcher ANR; never suppress an app failure."""
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


def close_target(xml: str, log: str) -> tuple[int, int] | None:
    if re.search(r'(?:ANR in |Process: )com\.osminog\.vision\b', log):
        return None
    if not re.search(r'ANR in com\.android\.launcher3\b', log):
        return None
    try:
        nodes = list(ET.fromstring(xml).iter('node'))
    except ET.ParseError:
        return None
    if any(n.get('package') != 'android' for n in nodes):
        return None
    title = [n for n in nodes if n.get('resource-id') == 'android:id/alertTitle']
    if len(title) != 1 or title[0].get('text') not in (
        "Quickstep isn't responding", "Quickstep isn’t responding"
    ):
        return None
    buttons = [n for n in nodes if n.get('resource-id') == 'android:id/aerr_wait'
               and n.get('clickable') == 'true' and n.get('enabled') == 'true']
    if len(buttons) != 1:
        return None
    match = re.fullmatch(r'\[(\d+),(\d+)\]\[(\d+),(\d+)\]', buttons[0].get('bounds', ''))
    if not match:
        return None
    x1, y1, x2, y2 = map(int, match.groups())
    if not (0 <= x1 < x2 <= 10000 and 0 <= y1 < y2 <= 10000):
        return None
    return ((x1 + x2) // 2, (y1 + y2) // 2)


if __name__ == '__main__':
    target = close_target(Path(sys.argv[1]).read_text(), Path(sys.argv[2]).read_text())
    if target is None:
        sys.exit(1)
    print(*target)
