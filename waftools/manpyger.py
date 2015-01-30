#!/usr/bin/env python
# encoding: utf-8
# Dominik Fischer, 2014-2015 (XZS)

"""
Support for Python modules and automatic manual page generation,

Loading this tool pulls in python and gnu_dirs. Note that you most probably have to call
check_python_version on the configuration context in order for any of the features herein to work.


Use the feature "py" to install python files, specified as sources, and
whole modules, specified as roots. If these are not found in the current
build path, it can be overwritten using the "install_from" parameter.

    bld(feature="py", install_from="src",
        root="package_one package_two", source="additional_file.py")
    Install the packages one and two and the additional_file, found in the src directory.


The feature "entrypynt" installs starters for python files and manual pages generated
from their argparse help text. Specify modules directly in the parameter "starter".

    bld(feature="entrypynt", starter="http.server compileall")
    Make some built-in python modules easily accessible as executable programs.

The parameter "main" instead generates a starter below each package given as "root".

    bld(feature="entrypynt", install_from="src",
        root="stable staging/experiment", main="main test")
    Generate starters and manual pages for stable.main, stable.test, found in a package located
    at src/stable, as well as experiment.main and experiment.test from src/staging/experiment.

When only roots are given, they are automatically scanned for
executable modules to generate starters and manual pages for.

    bld(feature="entrypynt", root=bld.path.ant_glob("package_*"))
    Find executable modules in all packages directly below the build path.

When automatically scanning for executable modules, each directory containing a file
named "__main__.py" is considered a match as well as every file that contains the
string "__name__ == '__main__'" specified with either double or single quotes. The
latter string identifying executable modules may be changed by assigning a pattern
object (as created by re.compile) to the attribute "main_indicator" of this module.

The short program description used in the manual page and by apropos can be overwritten
with the "short" parameter. Sections can be added using the "extra" parameter. Using an
OrderedDict for the latter is highly recommended to keep them from mixing up their order.

    bld(features="entrypynt", starter="nothing", short="does nothing",
            extra=OrderedDict((
                ('SEE ALSO', '.BR yes, echo'),
                ('BUGS', "The program should perhaps do something"))))


Both features can be conveniently combined to install an executable module in one line.

    bld(feature="py entrypynt", root=bld.path.ant_glob("package_*"))
    Install all packages found in the build path and add starters
    and manual pages for all executable modules found therein.


When generating a manual page, the tool tries to find all dependencies
by recursively scanning the given modules source for import statements.
The regular expression used to find these can be changed by assigning a
new pattern object (created by re.compile) to the attribute "import_statement"
of this module. It should be compiled with the MULTILINE flag and assign
the name of the module imported to a group named "module". By default,
instances of "from module import anything" and "import module" are found.

You may set it to an invalid pattern, like "$^", to turn off recursive scanning.
"""

from waflib.Task import Task
from waflib.TaskGen import feature, before_method, after_method, taskgen_method
from waflib.Utils import O755, subst_vars, to_list
from waflib.Context import g_module, APPNAME
from waflib.Node import Node
from waflib.Tools.python import feature_py
from re import compile, MULTILINE
from itertools import chain
from operator import methodcaller


def options(ctx):
    ctx.load('python gnu_dirs')

def configure(ctx):
    ctx.load('python gnu_dirs')
    ctx.check_python_module('manpager')

class entrypynt(Task):
    vars = ["PYTHON", "MODULE"]

    def run(self):
        starter = self.outputs[0]
        starter.write("#!/bin/sh\n" +
                subst_vars("exec ${PYTHON} -m ${MODULE} $@", self.env))
        starter.chmod(O755)

def find_py(location, module, entry="__init__"):
    """find a python module or entry point"""
    module = module.replace(".", "/")
    result = location.find_node(module)
    if result:
        return result.find_node(entry + ".py")
    else:
        return location.find_node(module + ".py")

import_statement = compile("^(import|(?P<from>from)) (?P<module>\..+)(?(from) import .+)$",
        MULTILINE)

class manpyge(Task):
    vars = ['env']  # This contains the PYTHONPATH which may cause a whole different module.
    # It can only be conveniently hashed like this because it contains only this
    # one element. Would it contain more, the unspecified order in a dictionary
    # could generate a different hash also when the elements do not change.

    run_str = "${PYTHON} -Bm manpager ${MANPAGERFLAGS} ${MODULE} > ${TGT}"

    def scan(self):
        """find local imports recursively"""
        module = find_py(self.generator.install_from, self.env.MODULE, "__main__")
        unseen = {module}
        seen = set()
        while unseen:
            module = unseen.pop()
            seen.add(module)
            for match in import_statement.finditer(module.read()):
                next = find_py(module.parent, match.group("module")[1:])
                if next not in seen:
                    unseen.add(next)
        return sorted(seen, key=methodcaller('srcpath')), None

    def keyword(self):
        return "Documenting module"

    def __str__(self):
        return self.env.MODULE

class gz(Task):
    run_str = "gzip -c ${SRC} > ${TGT}"

    def keyword(self):
        return "Compressing"


feature("entrypynt")(feature_py)
# This makes sure install_from is either None or a Node which generate_python_starter relies upon.

@feature("entrypynt")
@after_method("feature_py")
def compose_environment(self):
    parent = getattr(self, 'parent', None)
    if parent:
        self.env = parent.env
    else:
        env = self.env
        def flag(*args):
            env.append_value("MANPAGERFLAGS", args)
        short_desc = getattr(self, 'short', None)
        if short_desc:
            flag("-d", "'{}'".format(short_desc))
        appname = getattr(g_module, APPNAME, None)
        if appname:
            flag("-s", "'{}'".format(appname))
        for title, content in getattr(self, 'extra', {}).items():
            flag("-e", "'{} {}'".format(title.upper(), content))

        if self.install_from:
            path = self.install_from
        else:
            path = self.install_from = self.path
        env.env = {"PYTHONPATH": path.bldpath() + ":" + path.srcpath() + ":"}

@feature("entrypynt")
@after_method("compose_environment")
def generate_python_starter(self):
    env = self.env
    modules = to_list(getattr(self, "starter", []))
    for module, target in zip(modules, chain(self.target, map(self.install_from.find_or_declare,
        (module.replace(".", "-") for module in modules[len(self.target):])))):
        modenv = env.derive()
        modenv.MODULE = module
        modenv.append_value("MANPAGERFLAGS", ('-p', target.name))
        def create_task(*args, **kwargs):
            self.create_task(*args, env = modenv, **kwargs)
        starter = target.change_ext('.sh')
        create_task('entrypynt', tgt = starter)
        self.bld.install_as(subst_vars("${BINDIR}/", env) + target.name, starter, chmod=O755)
        manpage = target.change_ext('.1')
        create_task('manpyge', tgt = manpage)
        compressed = target.change_ext('.1.gz')
        create_task('gz', src = manpage, tgt = compressed)
        self.bld.install_files(subst_vars("${MANDIR}/man1", env), compressed)


@taskgen_method
def to_nodes(self, lst, path=None, search_fun="find_resource"):
    """This is exactly to_nodes, but finding directories without generating exceptions."""
    search_fun = getattr(path or self.path, search_fun)
    return [search_fun(dir) if isinstance(dir, str) else dir
            for dir in to_list([lst] if isinstance(lst, Node) else lst)]

@feature("py", "entrypynt")
@after_method("feature_py")
def split_root(self):
    roots = getattr(self, "root", None)
    if roots and not hasattr(self, "parent"):
        del(self.root)
        for root in self.to_nodes(roots, self.install_from, "find_dir"):
            self.bld(features = self.features, parent = self,
                    install_from = root.parent, root = root)

@feature("py")
@before_method("process_source")
def find_sources(self):
    parent = getattr(self, "parent", None)
    if parent:
        self.source = self.root.ant_glob("**/*.py")

def pop(lst, start, count):
    """Remove and return a slice from a list."""
    end = start + count
    result = lst[start:end]
    del(lst[start:end])
    return result

main_indicator = compile('__name__ == (?P<quote>["\'])__main__(?P=quote)')

@feature("entrypynt")
@after_method("feature_py")
@before_method("generate_python_starter")
def compose_starters(self):
    parent = getattr(self, "parent", None)
    if parent:
        mains = getattr(self.parent, "main", None)
        if mains:
            self.starter = [self.root.name + "." + main for main in to_list(mains)]
            self.target = pop(parent.target,
                    len(getattr(parent, "starter", ())), len(mains))
        elif not hasattr(self.parent, 'starter'):
            root = self.root
            base = root.parent
            def starter_path(node):
                if node.name == "__main__.py":
                    return node.parent.path_from(base)
                elif main_indicator.search(node.read()):
                    return node.path_from(base)[:-3]
            self.starter = [starter.replace("/", ".") for starter in
                    map(starter_path, root.ant_glob("**/*.py")) if starter]
    else:
        self.target = self.to_nodes(getattr(self, "target", ()),
                self.install_from, "find_or_declare")
        self.main = to_list(getattr(self, "main", ()))
