Font patcher for [powerline](https://github.com/Lokaltog/powerline) that patches 
BDF fonts

Installation
------------

To work with this font patcher you need the following python packages:

- [Python image library](https://bitbucket.org/effbot/pil-2009-raclette) or 
  [Pillow](https://pypi.python.org/pypi/Pillow).
- [bdflib](https://pypi.python.org/pypi/bdflib). Note that installation from pip 
  is currently broken, use

        pip install --user git+git://gitorious.org/bdflib/mainline.git

- [fontforge](http://fontforge.org) python bindings
- bdftopcf and pcf2bdf CLI tools (optional, but highly recommended)
- coreutils, zcat, bzip2 and POSIX-compatible shell

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
transformed back, `.bdf` ones will be patched, `.gz` or `.bz2` files are first 
uncompressed and then compressed back in the target directory. Files in source 
directory are not modified. Behavior in case source and target directories are 
the same directories is undefined, but you will likely just get a bunch of 
errors and corrupt or empty font files.


Additional requirements
-----------------------

If BDF font does not claim that it is written for `ISO10646` encoding it will 
not be patched.
