"""Convert millimetre text regions to the observed Kuixiang table schema.

Generates files only. It neither operates the app nor sends machine commands.
"""
import argparse
import copy
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PX_PER_MM = 96 / 25.4


def build(layout, preset):
    def number(obj, key, positive=False):
        value = obj[key]
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError(f'{key} must be a number')
        if not math.isfinite(value) or value < 0 or (positive and value == 0):
            raise ValueError(f'Invalid {key}: {value}')
        return value

    width = number(layout, 'width_mm', True)
    height = number(layout, 'height_mm', True)
    result = dict(orientation=0, width=width / 10, height=height / 10, items=[])
    rectangles = []
    for index, region in enumerate(layout['items'], 1):
        text = region['text']
        if not isinstance(text, str) or not text.strip():
            raise ValueError(f'Region {index}: text must not be empty')
        x, y = (number(region, k) for k in ('x_mm', 'y_mm'))
        w, h = (number(region, k, True) for k in ('width_mm', 'height_mm'))
        if x + w > width + 1e-8 or y + h > height + 1e-8:
            raise ValueError(f'Region {index} exceeds the frame')
        for old_index, ox, oy, ow, oh in rectangles:
            if x < ox + ow and ox < x + w and y < oy + oh and oy < y + h:
                raise ValueError(f'Regions {old_index} and {index} overlap')
        rectangles.append((index, x, y, w, h))
        page = copy.deepcopy(preset)
        # The saved native sample includes one 96-dpi pixel of content allowance.
        page.update(pageWidth=w + 1 / PX_PER_MM, pageHeight=h + 1 / PX_PER_MM)
        align = region.get('align', 'Left')
        if align not in ('Left', 'Center'):
            raise ValueError('align must be Left or Center')
        page['contentAlign'] = align
        if 'line_gap' in region:
            page['lineGap'] = number(region, 'line_gap', True)
        result['items'].append(dict(
            rotation=0, name=f'{index:03d}', type='text', text=text,
            x=round(x * PX_PER_MM, 4), y=round(y * PX_PER_MM, 4),
            width=round(w * PX_PER_MM, 4), height=round(h * PX_PER_MM, 4),
            pageInfo=page,
            contentFormat=json.dumps(dict(charset='UTF-8', autoGp=False,
                                          gpNum=0, firstLineAlign=align.upper())),
        ))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('layout', type=Path)
    parser.add_argument('--preset', type=Path, default=ROOT / 'presets/text-page-info.json')
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists():
        parser.error('Output already exists; choose a new filename to preserve previous versions.')
    layout = json.loads(args.layout.read_text(encoding='utf-8-sig'))
    preset = json.loads(args.preset.read_text(encoding='utf-8-sig'))
    result = build(layout, preset)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(f'Created {args.output}: {len(result["items"])} text regions. Check actual glyphs in the app.')


if __name__ == '__main__':
    main()
