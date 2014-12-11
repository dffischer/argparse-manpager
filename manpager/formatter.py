"""
classes formatting an ArgumentParser help text as a manual page

The classes in this module rank around implementing a HelpFormatter
that composes a man page instead of a console help text.
"""

from argparse import HelpFormatter
from functools import partial
from .structure import TH, SH

class ManPage(TH):
    """
    These TH will be initialized with a given set of default sections usually
    found in manual pages. Adding text will fill still empty sections, while
    the request to add a subsection will be redirected to an options subsection
    instead. Empty sections will not be included in the string serialization.
    """

    def __init__(self, prog, suite=None, short_desc=None, extrasections={}):
        """Initializes the subsections NAME, SYNOPSIS, OPTIONS and REMARKS.
        prog -- program name to describe
        suite -- optional suite name to use in the header instead of prog
        short_desc -- optional short description to add in NAME
        extrasections -- an optional mapping from titles to contents
            of additional sections to append at the end of the page"""

        name = SH('NAME') << prog
        synopsis = SH('SYNOPSIS')
        description = SH('DESCRIPTION')
        options = SH('OPTIONS')
        remarks = SH('REMARKS')
        super().__init__(suite if suite else prog, name, synopsis, description, options, remarks,
                *(SH(title) << content for title, content in extrasections.items()))
        if short_desc:
            name << "\-" << short_desc
        self.options = options
        self.next_section = iter((synopsis, description, remarks)).__next__

    def __lshift__(self, text):
        return self.next_section() << text

    def __truediv__(self, title):
        return self.options / title

    def __str__(self):
        return '\n'.join(str(item) for item in self if item)

class ManPageFormatter(HelpFormatter):
    """Help message formatter making the help text into a manual page.

    Keep in mind that this class almost entirely depends on parts of HelpFormatter
    and ArgumentParser explicitely stated not to be part of any documented API. Currently, it is
    only non-extensibly tested to work with python 3.4."""

    def __init__(self, prog, *args, **kwargs):
        """Remembers the program name and initializes the sect attribute to a fresh manpage.
        
        This class does by far not use all of the methods and attributes
        HelpFormatter does. The ones used only need the attribute _prog set.
        Not calling more complex parent methods or its constructor completely
        avoids the far detours HelpFormatter goes to consider the line width."""
        self._prog = prog
        self.sect = ManPage(prog, *args, **kwargs)

    def start_section(self, heading):
        """Adds a new subsection to the current section stored in the sect attribute and
        overrides it. A method end_section is established to restore the old sect value."""
        def reset(section):
            self.sect = section
            del(self.end_section)
        self.end_section = partial(reset, self.sect)
        self.sect /= heading

    def add_text(self, text):
        """Adds text element to the current section."""
        if text:
            self.sect << text

    def add_usage(self, usage, actions, groups, prefix=None):
        """Formats the usage and appends it to the current section."""
        self.sect << self._prog \
                << self._format_actions_usage(actions, groups)

    def add_arguments(self, actions):
        """Formats arguments and appends it to the current section."""
        for action in actions:
            self.sect << '.TP' \
                    << self._format_action_invocation(action) \
                    << self._expand_help(action)

    def format_help(self):
        """Serializes the current section.
        When the top level section is active, this returns the complete page as a string."""
        return str(self.sect)

