#!/usr/bin/env python3
"""Current glass material with all retained dim and trusted-click predicates."""
import runpy
from pathlib import Path
import re


def _rgba(value):
    found = re.fullmatch(r'rgba?\(\s*(\d+),\s*(\d+),\s*(\d+)(?:,\s*([01](?:\.\d+)?))?\s*\)', value or '')
    if found is None:
        raise ValueError('Settings computed color is missing')
    channels = tuple(int(part) for part in found.groups()[:3])
    alpha = float(found.group(4)) if found.group(4) is not None else 1.0
    if any(not 0 <= part <= 255 for part in channels) or not 0 <= alpha <= 1:
        raise ValueError('Settings computed color is outside its range')
    return channels, alpha


def _luminance(channels):
    scaled = [part / 255 for part in channels]
    linear = [part / 12.92 if part <= .04045 else ((part + .055) / 1.055) ** 2.4 for part in scaled]
    return sum(part * weight for part, weight in zip(linear, (.2126, .7152, .0722)))


def _mouse640_settings_surface(surface, toolbar, theme):
    need(theme in ('dark', 'light'), 'settings glass theme missing')
    blur = re.search(r'\bblur\((\d+(?:\.\d+)?)px\)', surface.get('backdropFilter', ''))
    need(blur is not None and 20 <= float(blur.group(1)) <= 40, 'settings glass blur is outside the current material contract')
    background, alpha = _rgba(surface.get('backgroundColor'))
    foreground, text_alpha = _rgba(surface.get('color'))
    _, border_alpha = _rgba(surface.get('borderColor'))
    need(.6 <= alpha < 1 and text_alpha == 1 and border_alpha > 0, 'settings glass, readable text or visible separating border absent')
    need(max(background) < 100 if theme == 'dark' else min(background) > 220, 'settings material does not match its dark/light theme')
    values = [_luminance(background), _luminance(foreground)]
    need((max(values) + .05) / (min(values) + .05) >= 4.5, 'settings text contrast is below 4.5:1')
    need(any(surface.get(key) != toolbar.get(key) for key in ('backgroundColor', 'backgroundImage')),
         'settings glass still uses the old toolbar surface')


runpy.run_path(str(Path(__file__).with_name("mouse640-reuse.py")))["execute"]('mouse637-sidebar-focus-evidence.py', globals())
