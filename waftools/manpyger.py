from waflib.Task import Task
from waflib.TaskGen import feature
from waflib.Utils import O755, subst_vars, to_list

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

class manpyge(Task):
    run_str = "PYTHONPATH=${gen.path.abspath()}: ${PYTHON} -Bm manpager ${MODULE} > ${TGT}"

    def keyword(self):
        return "Documenting module"

    def __str__(self):
        return self.env.MODULE

@feature('entrypynt')
def generate_python_starter(self):
    for module, target in zip(to_list(self.modules),
            map(self.path.find_or_declare, to_list(self.target))):
        env = self.env.derive()
        env.MODULE = module
        starter = target.change_ext('.sh')
        self.create_task('entrypynt', tgt = starter, env = env)
        self.bld.install_as(subst_vars("${BINDIR}/", self.env) + target.name, starter, chmod=O755)
        self.create_task('manpyge', tgt = target.change_ext('.1'), env = env)
