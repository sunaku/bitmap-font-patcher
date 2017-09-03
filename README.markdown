Font patcher for [powerline](https://github.com/Lokaltog/powerline) that patches 
BDF and PSF fonts

Installation
------------

To work with this font patcher you need the following python packages:

- [Python image library](https://bitbucket.org/effbot/pil-2009-raclette) or 
  [Pillow](https://pypi.python.org/pypi/Pillow).
- [bdflib](https://pypi.python.org/pypi/bdflib). Note that installation from pip 
  is currently broken, use

        pip install --user git+https://gitlab.com/Screwtapello/bdflib.git

    Optional, you don't need it unless you want to patch bdf font.

- [fontforge](http://fontforge.org) python bindings

The following software is required for patchdir.sh to work. It is optional but 
highly recommended.

- bdftopcf and pcf2bdf CLI tools
- [psftools](http://www.seasip.info/Unix/PSF/), namely psf2txt and txt2psf 
  utilities
- coreutils, zcat, bzip2 and any POSIX-compatible shell (busybox is known to 
  work)

Patching
--------

Patching is done either manually for one font, like this:

    zcat font.pcf.gz | pcf2bdf | python fontpatcher.py | bdftopcf | gzip > font-patched.pcf.gz

or using `patchdir.sh` script which will do this for you:

    sh patchdir.sh -f target-directory font.pcf.gz

(will create file `target-directory/font.pcf.gz`). To copy directory and patch 
fonts in it use

    sh patchdir.sh source-directory target-directory

. This will copy all files from `source-directory` to `target-directory`. Files 
ending with `.pcf` will be transformed into BDF files, patched and then 
transformed back, similar for `.psf` files (but they are transformed to TXT), 
`.bdf` ones will be patched, `.gz` or `.bz2` files are first uncompressed and 
then compressed back in the target directory. Files in source directory are not 
modified. Behavior in case source and target directories are the same 
directories is undefined, but you will likely just get a bunch of errors and 
corrupt or empty font files.


Additional requirements
-----------------------

If BDF font does not claim that it is written for `ISO10646` encoding it will 
not be patched. It may not claim they are written for any encoding at all 
though.

For TXT fonts must also claim they are using unicode. This is recognized by 
`Flags:` field set to 1 (see `man txt2psf`). Only PSF2 fonts are supported. Also 
note that you will likely need to replace some glyphs: putfont refuses to load 
font if there are more then 512 glyphs in it. For this job `patchfont.sh` and 
`fontpatcher.py` provide additional arguments:

    zcat psf-font.psf.gz | psf2txt | python fontpatcher.py txt 'AB;AC;AD'

or

    sh patchdir.sh -a 'AB;AC;AD' source-directory target-directory

or

    sh patchdir.sh -a 'AB;AC;AD' -f target-directory psf-font*

will replace glyphs with codepoints `AB`, `AC` and `AD` (patchdir determines 
font format based on extension). For BDF fonts replacing is not supported.
