#!/usr/bin/python
# vim: fileencoding=utf-8

import sys
from collections import Counter
from itertools import count
from PIL.Image import new as new_image
from PIL.ImageDraw import Draw
from PIL.ImageFont import truetype
import fontforge
import os
import operator

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

    def has_codepoint(self, codepoint):
        return codepoint in self.codepoints

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
        return self.fnt.properties.get('CHARSET_REGISTRY', 'ISO10646') == 'ISO10646'

    def dump(self, out):
        from bdflib.writer import write_bdf
        write_bdf(self.fnt, out)


class TxtGlyph(object):
    def __init__(self, width, height):
        self.width = width
        self.height = height

    def parse(self, f):
        for line in f:
            if line.startswith('//'):
                continue
            elif line.startswith('Bitmap: '):
                if hasattr(self, 'bitmap'):
                    raise ValueError('Double bitmap field')
                self.parse_bitmap(f, line[len('Bitmap: '):])
            elif line.startswith('Unicode: '):
                if hasattr(self, 'codepoints'):
                    raise ValueError('Double unicode field')
                self.parse_unicode(line[len('Unicode: '):])
            elif line == '%\n':
                break

        if not (hasattr(self, 'codepoints') and hasattr(self, 'bitmap')):
            raise ValueError('Codepoint and/or bitmap is not set')

    def parse_unicode(self, line):
        self.codepoints = []
        self.seqcodepoints = []
        for point in line.split(';'):
            point = point.lstrip('[').rstrip(']\n')
            if point:
                seq = point.split('+')
                if len(seq) > 1:
                    self.seqcodepoints.append(tuple((int(cp, 16) for cp in seq)))
                elif seq and seq[0]:
                    self.codepoints.append(int(seq[0], 16))

    def parse_bitmap(self, f, line):
        self.bitmap = [False] * (self.width * self.height)
        toparse = line
        pointer = 0
        while toparse:
            char = toparse[0]
            toparse = toparse[1:]
            if char == '-':
                pointer += 1
            elif char == '#':
                self.bitmap[pointer] = True
                pointer += 1
            elif char == '\\':
                toparse += next(f)
            elif char in ' \n\t\r':
                continue
            else:
                raise ValueError('Unknown bitmap character: ' + repr(char))

    def set_codepoint(self, codepoint):
        if hasattr(self, 'codepoints'):
            self.codepoints.add(codepoint)
        else:
            self.codepoints = set((codepoint,))
            self.seqcodepoints = set()

    def dump(self, out):
        out.write('Bitmap: ' + ''.join(('#' if char else '-' for char in self.bitmap)) + '\n')
        out.write('Unicode: ' + ';'.join(['[%x]' % cp for cp in  self.codepoints]
                                         + ['[' + ('+'.join(('%x' % cp for cp in seq))) + ']'
                                            for seq in self.seqcodepoints]) + '\n')
        out.write('%\n')


class TxtFont(object):
    headervals = ('Version', 'Flags', 'Length', 'Width', 'Height')
    def __init__(self, f):
        self.parse_header(f)
        self.glyphs = []
        self.codepoints = set()
        for i in range(self.length):
            glyph = self.parse_glyph(f)
            self.glyphs.append(glyph)
            self.codepoints.update(glyph.codepoints)

    def parse_header(self, f):
        if next(f) != '%PSF2\n':
            raise ValueError('Expected file start')

        headervals = set(self.headervals)

        for line in f:
            if line == '%\n':
                break
            key, val = line.partition(': ')[::2]
            val = int(val)
            if key not in headervals:
                raise ValueError('Unexpected key: ' + key)
            headervals.remove(key)
            setattr(self, key.lower(), val)

        if headervals:
            raise ValueError('Missing headers: ' + ', '.join(headervals))

    def parse_glyph(self, f):
        glyph = TxtGlyph(self.width, self.height)
        glyph.parse(f)
        return glyph

    def new_glyph_from_bitmap(self, bitmap, codepoint):
        glyph = TxtGlyph(self.width, self.height)
        glyph.set_codepoint(codepoint)
        glyph.bitmap = bitmap
        self.glyphs.append(glyph)
        self.codepoints.add(codepoint)
        self.length += 1

    def dump_header(self, out):
        out.write('%PSF2\n')
        for header in self.headervals:
            out.write(header + ': ' + str(getattr(self, header.lower())) + '\n')
        out.write('%\n')

    def dump(self, out):
        self.dump_header(out)
        for glyph in self.glyphs:
            glyph.dump(out)


class TxtPatcher(Patcher):
    def __init__(self):
        self.fnt = TxtFont(sys.stdin)
        self.codepoints = self.fnt.codepoints
        self.size = (self.fnt.width, self.fnt.height)

    def add_glyph(self, codepoint, name, img):
        bitmap = [False] * reduce(operator.mul, self.size)
        pointer = 0
        for y in range(self.size[1]):
            for x in range(self.size[0]):
                if not img.getpixel((x, y)):
                    bitmap[pointer] = True
                pointer += 1
        self.fnt.new_glyph_from_bitmap(bitmap, codepoint)

    def can_patch(self):
        # flags == 1 mean unicode font
        return self.fnt.flags == 1

    def dump(self, out):
        self.fnt.dump(out)


def select_patcher(argv):
    try:
        pclass = globals()[argv[0].title() + 'Patcher']
    except IndexError:
        pclass = BdfPatcher
    return pclass(*argv[1:])


patcher = select_patcher(sys.argv[1:])

if patcher.can_patch():
    patcher.set_font(powerline_font)
    patcher.patch()

patcher.dump(sys.stdout)
