"""Synthetic settings material mutations; never native screenshot evidence."""
import copy
from pathlib import Path
import runpy
import unittest

S = runpy.run_path(str(Path(__file__).with_name('mouse641-sidebar-focus-evidence.py')))


def surface(theme):
    return {'backdropFilter': 'blur(28px) saturate(1.35)', 'backgroundImage': 'linear-gradient(unit-fixture-only)',
            'backgroundColor': 'rgba(21, 29, 42, 0.95)' if theme == 'dark' else 'rgba(247, 249, 253, 0.94)',
            'color': 'rgb(230, 235, 244)' if theme == 'dark' else 'rgb(31, 42, 57)',
            'borderColor': 'rgba(255, 255, 255, 0.2)' if theme == 'dark' else 'rgba(70, 95, 130, 0.2)'}


class Material(unittest.TestCase):
    def test_dark_and_light_glass_have_separating_border_and_readable_text(self):
        for theme in ('dark', 'light'):
            S['_mouse640_settings_surface'](surface(theme), {'backgroundColor': 'rgb(15, 20, 28)', 'backgroundImage': 'none'}, theme)

    def test_solid_blur_missing_wrong_theme_invisible_border_and_low_contrast_rejected(self):
        for theme in ('dark', 'light'):
            for field, bad in [('backdropFilter', 'none'), ('backdropFilter', 'blur(4px)'),
                               ('backgroundColor', 'rgb(21, 29, 42)'),
                               ('backgroundColor', 'rgba(120, 120, 120, 0.95)'),
                               ('borderColor', 'rgba(255, 255, 255, 0)'),
                               ('color', 'rgb(80, 80, 80)' if theme == 'dark' else 'rgb(210, 210, 210)')]:
                value = surface(theme)
                value[field] = bad
                with self.subTest(theme=theme, field=field, bad=bad), self.assertRaises(ValueError):
                    S['_mouse640_settings_surface'](value, {}, theme)

    def test_old_identical_toolbar_material_cannot_pass_as_new_glass(self):
        for theme in ('dark', 'light'):
            value = surface(theme)
            with self.assertRaisesRegex(ValueError, 'old toolbar'):
                S['_mouse640_settings_surface'](value, copy.deepcopy(value), theme)


if __name__ == '__main__':
    unittest.main()
