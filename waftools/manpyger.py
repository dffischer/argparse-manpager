#!/usr/bin/env python
# encoding: utf-8
# Dominik Fischer, 2014-2015 (XZS)

from waflib.Task import Task
from waflib.TaskGen import feature, before_method, after_method, taskgen_method
from waflib.Utils import O755, subst_vars, to_list
from waflib.Context import g_module, APPNAME
from waflib.Node import Node
from waflib.Tools.python import feature_py
from re import compile, MULTILINE
from itertools import chain


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

class manpyge(Task):
    vars = ['env']  # This contains the PYTHONPATH which may cause a whole different module.
    run_str = "${PYTHON} -Bm manpager ${MANPAGERFLAGS} ${MODULE} > ${TGT}"

    def scan(self, imp=compile("^from (\..+) import .+$|^import (\..+)$", MULTILINE)):
        """find local imports recursively"""
        module = find_py(self.generator.install_from, self.env.MODULE, "__main__")
        unseen = {module}
        seen = set()
        while unseen:
            module = unseen.pop()
            seen.add(module)
            for match in imp.finditer(module.read()):
                next = find_py(module.parent, match.group(1)[1:])
                if next not in seen:
                    unseen.add(next)
        return seen, None

    def keyword(self):
        return "Documenting module"

    def __str__(self):
        return self.env.MODULE

class gz(Task):
    run_str = "gzip -c ${SRC} > ${TGT}"

    def keyword(self):
        return "Compressing"


feature('entrypynt')(feature_py)
# This makes sure install_from is either None or a Node which generate_python_starter relies upon.

@feature('entrypynt')
@after_method('feature_py')
def generate_python_starter(self):
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

    modules = to_list(self.starter)
    targets = to_list(self.target)
    for module, target in zip(modules, map(path.find_or_declare, chain(
        targets, (module.replace(".", "-") for module in modules[len(targets):])))):
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

@feature("entrypynt")
@after_method("feature_py")
@before_method("generate_python_starter")
def compose_starters(self):
    parent = getattr(self, "parent", None)
    if parent:
        mains = getattr(self.parent, "main", None)
        if mains:
            self.starter = [self.root.name + "." + main for main in to_list(mains)]
    else:
        self.main = to_list(getattr(self, "main", ()))
