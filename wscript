#! /usr/bin/env python

def options(ctx):
    ctx.load('python')

def configure(ctx):
    ctx.load('python')
    ctx.check_python_version()

def build(ctx):
    ctx(features="py", source=ctx.path.find_dir("manpager").ant_glob("**/*.py"))
