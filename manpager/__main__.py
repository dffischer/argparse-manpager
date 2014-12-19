#!/usr/bin/python
"""Generates a manual page from a module using argparse."""

from functools import partial, partialmethod
from argparse import ArgumentParser
from .formatter import ManPageFormatter
from runpy import run_module
from sys import argv

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
    return ManPageFormatter(prog=self.prog)

run_module(argv[1], run_name='__main__', alter_sys=True) # alter_sys to update program name in argv[0]
