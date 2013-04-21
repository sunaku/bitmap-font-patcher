#!/bin/sh
powerline_patcher="`dirname $0`/fontpatcher.py"
if test "x$1" = "x-f" ; then
    shift
    dst="$1"
    shift
else
    src="$1"
    dst="$2"
fi

test -d "$dst" || mkdir -p "$dst" || exit $?

procfile()
{
    srcf="$1"
    dstf="$dst/`basename $srcf`"

    unzip="cat"
    zip="cat"
    transform="cat"
    untransform="cat"
    patcher="cat"
    pargs=

    if test -d "$srcf" ; then
        (
            dst="$dstf"
            src="$srcf"
            test -d "$dst" || mkdir -p "$dst" || exit $?
            for srcf in "$src/"* ; do
                procfile "$srcf"
            done
        )
        return $?
    fi

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
        (*.psf)
            transform="psf2txt"
            untransform="txt2psf"
            patcher="$powerline_patcher"
            pargs="txt"
            ;;
        (*)
            ;;
    esac
    $unzip < "$realsrcf" | $transform | "$patcher" $pargs | $untransform | $zip > "$dstf"
}

if test "x$src" = "x" ; then
    for srcf in "$@" ; do
        procfile "$srcf"
    done
else
    for srcf in "$src"/* ; do
        procfile "$srcf"
    done
fi
