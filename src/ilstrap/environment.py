import dataclasses
import sys
import typing
from os import path
import importlib.util

import idaapi
from ilstrap.shared import IStrapProject, IStrapConfig

ISTRAP_ROOT = path.dirname(__file__)
PLUGIN_ROOT = path.realpath(path.join(ISTRAP_ROOT, '..'))


@dataclasses.dataclass
class IStrapLoader:
    name: str
    accept_file: typing.Callable
    load_file: typing.Callable


def _path_to_module_name(plugin_name, loader_path) -> str:
    name = next(reversed(path.split(loader_path))).removesuffix('.py')
    return f"{plugin_name}__{name}"


class IStrapEnvironment:
    _environment = None

    config: IStrapConfig
    plugins: list[idaapi.plugin_t] = []
    _loaders: typing.Optional[dict[str, IStrapLoader]] = None
    _format_map = {}

    def __init__(self, plugin_path):
        self.plugin_path = plugin_path
        self.istrap_root = path.join(plugin_path, 'ilstrap')
        self.config_path = path.join(self.istrap_root, 'istrap.json')
        self.config = IStrapConfig.load_from(self.config_path)
        print('configuration loaded as: ', self.config)

    def _package_to_configuration(self, name):
        package_path = path.join(self.istrap_root, name)
        if not path.isdir(package_path) or path.islink(package_path):
            return None

        return IStrapProject.from_project_path(package_path)

    def produce_package_configs(self):
        for package in self.config.packages:
            package_config = self._package_to_configuration(package)
            if not package_config:
                print(f"Could not load ilstrap package {package}")

            yield package_config

    def prepare_load_path(self):
        for package in self.produce_package_configs():
            print(f"ilstrap loading package: {package.name} ({package.version})")
            for module in package.module_paths:
                if module not in sys.path:
                    print(f"package appending load path: {module}")
                    sys.path.append(module)

            print('final load path: ', sys.path)

    def set_loader(self, format_name, loader):
        self._format_map[format_name] = loader

    def get_for_format(self, format_name):
        return self._format_map[format_name]

    @property
    def loaders(self) -> dict[str, IStrapLoader]:
        if not self._loaders:
            self._loaders = {}

            for package in self.produce_package_configs():
                print(f"Processing loaders for plugin {package.name}")
                for loader in package.loaders:
                    print(f"Preparing loader {loader} for plugin {package}")
                    loader_path = path.realpath(path.join(self.istrap_root, package.name, loader))
                    module_name = _path_to_module_name(package.name, loader_path)
                    spec = importlib.util.spec_from_file_location(module_name, loader_path)

                    loader_module = importlib.util.module_from_spec(spec)

                    spec.loader.exec_module(loader_module)

                    self._loaders[module_name] = IStrapLoader(module_name,
                                                              loader_module.accept_file,
                                                              loader_module.load_file)

        return self._loaders

    def prepare_loaders(self):
        assert self.loaders

    def get_loader(self, name):
        return self._loaders[name]

    @classmethod
    def environment(cls):
        if not cls._environment:
            cls._environment = cls(PLUGIN_ROOT)

        return cls._environment
