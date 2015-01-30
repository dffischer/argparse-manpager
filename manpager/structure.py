"""
manual page sectioning structure

The classes in this module model the headers, sections and subsections a manual page is
composed of, so that they can be dynamically created and modified, mainly by adding subelements.
"""

from datetime import date

class Container(list):
    """
    Element containing further elements, which are exposed through a list interface. The left
    shift operator can also be used to append new contents, as container << element == element.

    The first element is a title, composed on construction by the header
    function using the tag attribute, which subclasses may want to override.
    """

    def __init__(self, title, *args):
        """Compose a title and adds all further given arguments after it."""
        super().__init__((self.header(title), ) + args)

    def __lshift__(self, element):
        """Add a subelement returning it."""
        self.append(element)
        return self

    def header(self, title):
        """Compose a header of the form '.{self.tag} {title}'"""
        return '.{tag} {title}'.format(tag=self.tag, title=title)

    def __str__(self):
        """Print the container and all its contents recursively."""
        return '\n'.join(map(str, self))

    def __bool__(self):
        """The container is considered truthy if it contains anything more than the title."""
        return len(self) > 1

class SectionContainer(Container):
    """
    These containers support adding subsections sing container /
    title, which will add and return a new subsection.

    To work, subsections need a method named subtype. It is considered a creation
    function to initialize a freshly initialized subsection when passed a title.
    """

    def __truediv__(self, title):
        """Add a new subsection with the given title and return it."""
        subsection = self.subtype(title)
        self << subsection
        return subsection

class SS(Container):
    """subsection"""
    tag = 'SS'

class SH(SectionContainer):
    """section"""
    tag = 'SH'
    subtype = SS

class TH(SectionContainer):
    """title, i.e. a whole man page"""
    subtype = SH
    @staticmethod
    def header(title):
        return '.TH "{prog}" 1 {date} "" "General Commands Manual"'.format(
                prog=title, date=date.today().isoformat())
