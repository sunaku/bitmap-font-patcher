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
import os

try:
    from __builtin__ import unichr
except ImportError:
    unichr = chr

powerline_font = os.path.join(os.path.dirname(__file__), 'powerline', 'font', 'PowerlineSymbols.otf')

class SkipIter(object):
    def __init__(self, it):
        self.it = it

    def next(self):
        r = self.it.next()
        while not r.rstrip():
            r = self.it.next()
        return r

    def __iter__(self):
        return self

fnt = read_bdf(SkipIter(sys.stdin))

if fnt.properties['CHARSET_REGISTRY'] == 'ISO10646':
    sizes = Counter(((glyph.advance, glyph.get_bounding_box()) for glyph in fnt.glyphs))
    advance, bb = sizes.most_common()[0][0]
    size = bb[2:]

    tt = truetype(powerline_font, size[1])
    ff = fontforge.open(powerline_font)

    codepoints = set(fnt.codepoints())

    rowWidth, extraBits = divmod(size[0], 8)
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
        for y in range(size[1]):
            value = 0
            for x in range(size[0]-1, -1, -1):
                value |= (0 if img.getpixel((x, y)) else 1) << (size[0] - x - 1)
            data.insert(0, get_data_line(value))
        data.reverse()
        fnt.new_glyph_from_data(name=name,
                                data=data,
                                bbX=bb[0],
                                bbY=bb[1],
                                bbW=bb[2],
                                bbH=bb[3],
                                advance=advance,
                                codepoint=codepoint)
write_bdf(fnt, sys.stdout)
