#! /usr/bin/env python

def options(ctx):
    ctx.load('manpyger')

def configure(ctx):
    ctx.load('manpyger')
    ctx.check_python_version()

def build(ctx):
    ctx(features="py", source=ctx.path.find_dir("manpager").ant_glob("**/*.py"))
    ctx(features="entrypynt", modules="manpager", target="manpager.sh")
