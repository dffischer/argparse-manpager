#!/usr/bin/python
"""Generates a manual page from a module using argparse."""

from argparse import ArgumentParser

# Do not modify ArgumentParser yet. First, it is needed proper for this program itself.

parser = ArgumentParser(description="Generates a manpage from an argparse help text")
parser.add_argument('module', help="module to generate manpage for")
parser.add_argument('-d', '--short', metavar="DESCRIPTION", help="""
        Specifies a short description to add in the NAME section. This will be
        the summary shown by apropos. When not given, this will just consist
        of the executable name. The inherent description text given at ArgumentParser
        construction will always end up in the DESCRIPTION section.""")
args = parser.parse_args()
del(parser)


# Parsing finished. Now the parser class can be patched.

from functools import partial, partialmethod
from .formatter import ManPageFormatter

def override(cls, name, method):
    """Injects a method into a class.

    This will inject the given method into the given class, overriding a member
    of the given name. The new method will receive the same arguments as the old
    variant, with the original member passed in as second argument right after self.
    If the class previously had no member of this name, this argument will be None.
    """
    setattr(cls, name, partialmethod(method, getattr(cls, name, None)))
    return method

def inject(cls):
    """Decorate a method to be injected.

    Using this decorator on a function will inject in as a method into
    the given class, overriding an existing method with the same name.
    """
    return lambda method: override(cls, method.__name__, method)

argparser = inject(ArgumentParser)

@argparser
def parse_known_args(self, original, argv=None, namespace=None):
    return original(self, ('-h', ), namespace)

@argparser
def _get_formatter(self, original):
    return ManPageFormatter(prog=self.prog, short_desc=args.short)


# Execute the given module.

from runpy import run_module

run_module(args.module, run_name='__main__',
        alter_sys=True) # alter_sys to update program name in argv[0]
