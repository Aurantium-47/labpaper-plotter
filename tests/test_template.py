import copy
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('build_template', ROOT / 'scripts/build_template.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class TemplateTest(unittest.TestCase):
    def setUp(self):
        self.layout = json.loads((ROOT / 'examples/layout.json').read_text(encoding='utf-8'))
        self.preset = json.loads((ROOT / 'presets/text-page-info.json').read_text(encoding='utf-8'))

    def test_import_units_and_fonts(self):
        before = copy.deepcopy(self.preset)
        result = module.build(self.layout, self.preset)
        self.assertEqual((result['width'], result['height']), (14.9, 20.75))
        self.assertAlmostEqual(result['items'][0]['x'] * 25.4 / 96, 3, places=4)
        for item in result['items']:
            self.assertEqual(item['pageInfo']['fontPath'], self.preset['fontPath'])
        self.assertEqual(before, self.preset)

    def test_reject_out_of_frame(self):
        self.layout['items'][0]['x_mm'] = 148
        with self.assertRaisesRegex(ValueError, 'exceeds'):
            module.build(self.layout, self.preset)

    def test_reject_overlap(self):
        self.layout['items'][1]['y_mm'] = 5
        with self.assertRaisesRegex(ValueError, 'overlap'):
            module.build(self.layout, self.preset)

    def test_reject_nonfinite_coordinate(self):
        self.layout['items'][0]['x_mm'] = float('nan')
        with self.assertRaises(ValueError):
            module.build(self.layout, self.preset)


if __name__ == '__main__':
    unittest.main()
