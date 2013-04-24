#!/usr/bin/python
# vim: fileencoding=utf-8

from PIL.BdfFontFile import BdfFontFile
from PIL.ImageDraw import Draw
import sys
import os
from itertools import product


if sys.version_info < (3,):
    # Workaround should work only with pillow (as PIL is said to be not 
    # compatible with python-3*). This requirement is here due to the fact that 
    # in python-2* class FontFile and thus BdfFontFile is old-style class where 
    # @properties do not work.
    raise SystemError('Must use at least version 3')


class WorkaroundDict(dict):
    @staticmethod
    def __len__():
        # Must be more then maximum codepoint value in the set of interesting 
        # glyphs
        return 0xFFFF


class BDFWorkaround(BdfFontFile):
    # PIL is currently unable to work with unicode fonts, accepting only latin-1 
    # glyphs. This is a workaround.

    # The following is used once per script invocation thus no need to set it in 
    # __init__
    _glyph = WorkaroundDict()

    @property
    def glyph(self):
        return self._glyph

    @glyph.setter
    def glyph(self, value):
        # Don’t let property be set to a list of None’s
        pass


fnt = BDFWorkaround(open(sys.argv[1], 'rb'))
for cps in sys.argv[2:]:
    cp = int(cps, 16)
    if cp not in fnt.glyph:
        continue
    xy, dst, src, img = fnt.glyph[cp]
    size = src[2:]
    d = os.path.join(os.path.dirname(__file__), 'glyphs', 'x'.join((str(i) for i in size)))
    f = os.path.join(d, '%08x' % cp)
    if not os.path.isdir(d):
        os.mkdir(d)
    draw = Draw(img)
    for pos in product(range(img.size[0]), range(img.size[1])):
        if img.getpixel(pos):
            draw.point(pos, 0)
        else:
            draw.point(pos, 255)
    img.save(f, 'BMP')
