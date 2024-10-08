#! /usr/bin/env python

# The next two lines enable the use of the manpyger waftool before installing it. When you
# use the tool in your own projects and argparse-mapager is installed, you do not need them.
from sys import path
path.append("waftools")

APPNAME = "argparse-manpager"

from collections import OrderedDict
from waflib.Context import waf_dir
from waflib.Utils import subst_vars

def options(ctx):
    ctx.load('manpyger')

def configure(ctx):
    ctx.load('manpyger')
    ctx.check_python_version()

def build(ctx):
    ctx(features="py entrypynt", root="manpager", starter="manpager",
            extra=OrderedDict((
                ('SEE ALSO', '.BI pydoc \\ argparse'),
                ('AUTHORS', """The manpager was initially developed by XZS <d.f.fischer@web.de>.

                The code lives on github <http://github.com/dffischer/argparse-manpager>."""))))
    ctx.install_files(''.join((subst_vars("${LIBDIR}/", ctx.env),
        waf_dir.rpartition('/')[2], "/waflib/extras")), 'waftools/manpyger.py')
