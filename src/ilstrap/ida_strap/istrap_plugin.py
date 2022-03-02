import sys
import typing
from os import path

import idaapi

PLUGIN_ROOT = path.dirname(__file__)

print('[ilstrapplugin] begin plugin shim...')

sys.path.insert(0, PLUGIN_ROOT)

from ilstrap.environment import IStrapEnvironment


if not 'IStrapRootPlugin' in dir():
    class IStrapRootPlugin(idaapi.plugin_t):
        flags = idaapi.PLUGIN_HIDE
        comment = "IStrap Bootstrap Plugin"
        help = "Runs to update and load various istrap packages"
        wanted_name = "IBootStrap"
        wanted_hotkey = ""

        _environment: "IStrapEnvironment"

        def __init__(self, environment):
            self._environment = environment

        def init(self):
            self._environment.prepare_load_path()
            packages = list(self._environment.produce_package_configs())

            for package in packages:
                for plugin in package.plugins:
                    print(f"package creating plugin {plugin}")
                    resolved_plugin = path.realpath(path.join(package.source_path, plugin))
                    plugin_instance = idaapi.load_plugin(resolved_plugin)
                    print(f'load_plugin of plugin {plugin} ', plugin_instance)

            return idaapi.PLUGIN_KEEP

        def run(self, arg):
            pass

        def term(self):
            pass


# noinspection PyPep8Naming
def PLUGIN_ENTRY():
    root_plugin = IStrapRootPlugin(IStrapEnvironment.environment())

    return root_plugin
