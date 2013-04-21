#!/usr/bin/python
# vim: fileencoding=utf-8

from bdflib.reader import read_bdf
from bdflib.writer import write_bdf
import sys
from collections import Counter
from PIL.Image import new as new_image
from PIL.ImageDraw import Draw
from PIL.ImageFont import truetype
import fontforge

try:
    from __builtin__ import unichr
except ImportError:
    unichr = chr

font_file = sys.argv[1]
out_font_file = sys.argv[2]
powerline_font = '/home/zyx/.vam/powerline/font/PowerlineSymbols.otf'

class SkipFile(file):
    def next(self):
        r = super(SkipFile, self).next()
        while not r.rstrip():
            r = super(SkipFile, self).next()
        return r

fnt = read_bdf(SkipFile(font_file, 'rb'))

sizes = Counter(((glyph.advance, glyph.get_bounding_box()) for glyph in fnt.glyphs))
advance, bb = sizes.most_common()[0][0]
size = bb[-1:-3:-1]

tt = truetype(powerline_font, size[1])
ff = fontforge.open(powerline_font)

codepoints = set(fnt.codepoints())

rowWidth, extraBits = divmod(size[1], 8)
fnt.glyphs[0].get_data()
if extraBits > 0:
    rowWidth += 1
    paddingBits = 8 - extraBits
else:
    paddingBits = 0

def get_data_line(value):
    return "%0*X" % (rowWidth * 2, value << paddingBits)

for codepoint, name in ((cp, name) for cp, name in ((glyph.unicode, glyph.glyphname) for glyph in ff.glyphs())
                        if cp > 0 and cp not in codepoints):
    img = new_image('1', size, '#FFFFFF')
    draw = Draw(img)
    draw.text((0, 0), unichr(codepoint), font=tt, fill='#000000')
    data = []
    for x in range(size[0]):
        value = 0
        for y in range(size[1]):
            value |= (1 if img.getpixel((x, y)) else 0) << y
        data.append(get_data_line(value))
    data.reverse()
    fnt.new_glyph_from_data(name=name,
                            data=data,
                            bbX=bb[0],
                            bbY=bb[1],
                            bbW=size[1],
                            bbH=size[0],
                            advance=advance,
                            codepoint=codepoint)

with open(out_font_file, 'wb') as out:
    write_bdf(fnt, out)
