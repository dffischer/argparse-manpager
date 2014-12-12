"""
manual page text formatting utilities

The functions in this module format text according
to roff syntax, which is used in manual pages.
"""

from functools import partial

def listmap(func, list):
    """the built-in map function, returning a tuple instead of an iterable"""
    return tuple(func(element) for element in list)

def bold(text):
    """formats a span of running text bold"""
    return r'\fB{}\fP'.format(text)

def italic(text):
    """formats a span of running text italic"""
    return r'\fI{}\fP'.format(text)

class OverrideWrapper(object):
    """A generic wrapper that can selectively modify attributes of the wrapped object.

    If a method exists in the wrapper, requesting it will have the same effect as calling it with
    the member of the same name from the wrapped object as an argument. All other attributes,
    including such that are set None explicitly, are retrieved directly from the wrapped object.
    """

    def __init__(self, wrapped):
        """Wraps a given object modifying all attributes defined in the wrapper."""
        self.wrapped = wrapped

    @classmethod
    def generate(cls, name='GeneratedOverrider', **kw):
        """Create a wrapper class overriding methods given as keyword arguments."""
        return type(name, (cls, ), kw)

    def __getattribute__(self, name):
        original = getattr(super().__getattribute__('wrapped'), name)
        if original:
            try:
                return super().__getattribute__(name)(original)
            except AttributeError:
                return original

class FormatWrapper(OverrideWrapper):
    """Wrap an Action to format option strings bold and metavar italic."""
    option_strings = staticmethod(partial(listmap, bold))
    metavar = staticmethod(italic)
