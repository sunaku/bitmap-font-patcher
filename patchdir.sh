#!/bin/sh
src="$1"
dst="$2"
tmp="`mktemp`"
powerline_patcher="`dirname $0`/fontpatcher.py"

test -d "$dst" || mkdir -p "$dst" || exit $?

for srcf in "$src"/* ; do
    unzip="cat"
    zip="cat"
    transform="cat"
    untransform="cat"
    patcher="cat"
    echo ">>> $srcf"
    realsrcf="$srcf"
    case "$srcf" in
        (*.gz)
            unzip="zcat"
            zip="gzip"
            srcf="${srcf%.gz}"
            ;;
        (*.bz2)
            unzip="bzcat"
            zip="bzip2"
            srcf="${srcf%.bz2}"
            ;;
    esac
    case "$srcf" in
        (*.pcf)
            transform="pcf2bdf"
            untransform="bdftopcf"
            patcher="$powerline_patcher"
            ;;
        (*.bdf)
            patcher="$powerline_patcher"
            ;;
        (*)
            ;;
    esac
    dstf="$dst/`basename $realsrcf`"
    $unzip < "$realsrcf" | $transform | "$patcher" | $untransform | $zip > "$dstf"
done
