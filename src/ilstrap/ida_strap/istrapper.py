import sys
import typing
from os import path
import importlib.util

import idaapi

PLUGIN_ROOT = path.dirname(__file__)
ISTRAP_ROOT = path.join(PLUGIN_ROOT, 'ilstrap')
LOCAL_CONFIG = path.join(ISTRAP_ROOT, 'istrap.json')

sys.path.insert(0, PLUGIN_ROOT)

from ilstrap.shared import IStrapConfig, IStrapProject, IStrapProjectEntry


class IStrapRootPlugin(idaapi.plugin_t):
    flags = idaapi.PLUGIN_HIDE
    comment = "IStrap Bootstrap Plugin"
    help = "Runs to update and load various istrap packages"
    wanted_name = "IBootStrap"
    wanted_hotkey = ""

    _environment: "IStrapEnvironment"

    def set_environment(self, env):
        self._environment = env

    def init(self):
        packages = list(self._environment.produce_package_configs())

        for package in packages:
            print(f"ilstrap loading package: {package.name} ({package.version})")
            for module in package.module_paths:
                if module not in sys.path:
                    print(f"package appending load path: {module}")
                    sys.path.append(module)

            for plugin in package.plugins:
                print(f"package creating plugin {plugin.path}")
                resolved_plugin = path.realpath(path.join(package.source_path, plugin.path))
                plugin_instance = idaapi.load_plugin(resolved_plugin)
                print(f'load_plugin of plugin {plugin.path} ', plugin_instance)

            for loader in package.loaders:
                print(f"package creating loader {loader.path}")
                resolved_loader = path.realpath(path.join(package.source_path, loader.path))
                loader_instance = idaapi.load_plugin(resolved_loader)
                print(f'load_plugin of loader {loader.path} ', loader_instance)

        return idaapi.PLUGIN_KEEP

    def run(self, arg):
        pass

    def term(self):
        pass


def _package_to_configuration(name):
    package_path = path.join(ISTRAP_ROOT, name)
    if not path.isdir(package_path) or path.islink(package_path):
        return None

    return IStrapProject.from_project_path(package_path)


class IStrapEnvironment:
    config: IStrapConfig
    root_plugin: typing.Optional[IStrapRootPlugin] = None
    plugins: list[idaapi.plugin_t] = []

    def __init__(self):
        self.config = IStrapConfig.load_from(LOCAL_CONFIG)
        self.root_plugin = idaapi.find_plugin('istrapper')

    def produce_plugin(self) -> IStrapRootPlugin:
        if not self.root_plugin:
            self.root_plugin = IStrapRootPlugin()
            self.root_plugin.set_environment(self)
        return self.root_plugin

    def produce_package_configs(self):
        for package in self.config.packages:
            package_config = _package_to_configuration(package)
            if not package_config:
                print(f"Could not load ilstrap package {package}")

            yield package_config


environment = IStrapEnvironment()


# noinspection PyPep8Naming
def PLUGIN_ENTRY():
    return environment.produce_plugin()
