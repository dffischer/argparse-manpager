from waflib.Task import Task
from waflib.TaskGen import feature
from waflib.Utils import O755, subst_vars, to_list
from waflib.Context import g_module, APPNAME
from re import compile, MULTILINE

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
    run_str = "PYTHONPATH=${gen.path.abspath()}: ${PYTHON} " \
        "-Bm manpager ${MANPAGERFLAGS} ${MODULE} > ${TGT}"

    def scan(self, imp=compile("^from (\..+) import .+$|^import (\..+)$", MULTILINE)):
        """find local imports recursively"""
        module = find_py(self.generator.path, self.env.MODULE, "__main__")
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

@feature('entrypynt')
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

    modules = to_list(self.modules)
    for module, target in zip(modules, map(self.path.find_or_declare,
        to_list(self.target) if self.target else (
            module.replace(".", "-") for module in modules))):
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
