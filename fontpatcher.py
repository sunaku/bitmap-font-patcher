#!/usr/bin/python
# vim: fileencoding=utf-8

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

class Patcher(object):
    def get_image(self):
        return new_image('1', self.size, '#FFFFFF')

    def draw_glyph(self, img, codepoint):
        draw = Draw(img)
        draw.text((0, 0), unichr(codepoint), font=self.tt, fill='#000000')
        return img

    def add_codepoint(self, codepoint, name):
        return self.add_glyph(codepoint, name, self.draw_glyph(self.get_image(), codepoint))

    def set_font(self, fontfile):
        self.tt = truetype(fontfile, self.size[1])
        self.ff = fontforge.open(fontfile)

    def list_codepoints(self):
        for glyph in self.ff.glyphs():
            cp = glyph.unicode
            if cp > 0 and not self.has_codepoint(cp):
                yield cp, glyph.glyphname

    def patch(self):
        for codepoint, name in self.list_codepoints():
            self.add_codepoint(codepoint, name)


class BdfPatcher(Patcher):
    def __init__(self):
        from bdflib.reader import read_bdf
        self.fnt = read_bdf(SkipIter(sys.stdin))
        sizes = Counter(((glyph.advance, glyph.get_bounding_box()) for glyph in self.fnt.glyphs))
        self.advance, self.bb = sizes.most_common()[0][0]
        self.size = self.bb[2:]
        self.codepoints = set(self.fnt.codepoints())

        rowWidth, extraBits = divmod(self.size[0], 8)
        if extraBits > 0:
            rowWidth += 1
            paddingBits = 8 - extraBits
        else:
            paddingBits = 0

        def get_data_line(value):
            return "%0*X" % (rowWidth * 2, value << paddingBits)
        self.get_data_line = get_data_line

    def has_codepoint(self, codepoint):
        return codepoint in self.codepoints

    def add_glyph(self, codepoint, name, img):
        data = []
        for y in range(self.size[1]):
            value = 0
            for x in range(self.size[0]-1, -1, -1):
                value |= (0 if img.getpixel((x, y)) else 1) << (self.size[0] - x - 1)
            data.insert(0, self.get_data_line(value))
        data.reverse()
        self.fnt.new_glyph_from_data(name=name,
                                     data=data,
                                     bbX=self.bb[0],
                                     bbY=self.bb[1],
                                     bbW=self.bb[2],
                                     bbH=self.bb[3],
                                     advance=self.advance,
                                     codepoint=codepoint)

    def can_patch(self):
        return self.fnt.properties['CHARSET_REGISTRY'] == 'ISO10646'

    def write(self, out):
        from bdflib.writer import write_bdf
        write_bdf(self.fnt, out)


patcher = BdfPatcher()

if patcher.can_patch():
    patcher.set_font(powerline_font)
    patcher.patch()

patcher.write(sys.stdout)
