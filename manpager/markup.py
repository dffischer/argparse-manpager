"""
manual page text formatting utilities

The functions in this module format text according
to roff syntax, which is used in manual pages.
"""

from functools import partial
from re import compile, MULTILINE

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


from collections import OrderedDict

class MultiRegexReplacer(object):
    """Replace multiple regular expressions in one pass."""

    def __init__(self, replaces):
        """Replaces a given mapping.

        Keys are regular expressions to replace, values are their replacements. These may be
        callables which will be used to generate a replacement. Note that, other than with
        re.sub, they will not be passed a match object, but the original match as a string.
        Values that are not callable will be used as replacements without further modification.
        """
        expressions, self.replacements = zip(*replaces.items())
        self.expression = compile('|'.join(map('({})'.format, expressions)), MULTILINE)

    def replace(self, match):
        """Generate the replacement for a single match according
        to the replacement directives given on initialization."""
        for group, replacement in zip(match.groups(), self.replacements):
            if group:
                try:
                    return replacement(group)
                except TypeError:
                    return replacement

    def __call__(self, text):
        return self.expression.sub(self.replace, text)

class Sanitizer(MultiRegexReplacer):
    """Sanitize strings for usage in manual pages.

    This will trim whitespace on beginning and end, escape special characters,
    condense whitespace and turn double newlines into proper paragraphs.
    """

    def __init__(self, paragraph=".PP"):
        """Initialize a new Sanitizer generating the given paragraph type.

        Top-level paragraphs are the default. Use ".IP" for indented sections.
        """
        paragraph = '\n' + paragraph + '\n'
        super().__init__(OrderedDict((
            ('-', '\\-'),
            ('\n\n+', paragraph),
            ('^\s+|\s+$', ''),
            ('\s\s+', ' '))))
