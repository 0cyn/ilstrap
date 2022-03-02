import argparse
import pkgutil
import re
import sys
from os import path
from sys import platform

from .shared import *
from .windows import Windows

DARWIN_APPLICATIONS = "/Applications"
DARWIN_IDA_INSTALL = re.compile(r"^IDA Pro \d+\.\d+")
GITHUB_REPO_PATTERN = re.compile(r"(\w+)/(\w+)")

IDA_MODULES = ['__init__.py', 'shared.py', 'environment.py']
IDA_SHIMS = {'plugins': 'istrap_plugin.py', 'loaders': 'istrap_loader.py'}


class IDA:
    @staticmethod
    def is_ida_path(ida_path):
        if sys.platform == 'win32':
            ida64 = 'ida64.exe'
        else:
            ida64 = 'ida64'

        return path.isfile(path.join(ida_path, ida64))

    @staticmethod
    def guess_ida_install_dir():
        if sys.platform == 'darwin':
            possible_ida = [candidate for candidate
                            in os.listdir('/Applications')
                            if DARWIN_IDA_INSTALL.match(candidate)]

            for possible in possible_ida:
                idabin = path.join('/Applications', possible, 'idabin')
                if path.islink(idabin):
                    return path.join('/Applications', possible, os.readlink(idabin))

        return None

    ida_path: str
    _configuration = None

    def __init__(self, ida_path):
        self.ida_path = ida_path

    @property
    def install_path(self):
        return path.join(self.ida_dir('plugins'), 'ilstrap')

    @property
    def config_path(self):
        return path.join(self.install_path, 'istrap.json')

    def ida_dir(self, name):
        return path.join(self.ida_path, name)

    @property
    def configuration(self):
        if not self._configuration:
            self._configuration = IStrapConfig.load_from(self.config_path)
            self.save_configuration()

        return self._configuration

    def save_configuration(self):
        self.configuration.save(self.config_path)

    def install_istrap(self):
        if not path.isdir(self.install_path):
            os.mkdir(self.install_path)

        for shim in IDA_SHIMS:
            shim_destination_path = path.join(self.ida_dir(shim), IDA_SHIMS[shim])
            with open(shim_destination_path, 'wb') as ida_shim:
                shim_source_path = path.join('ida_strap', IDA_SHIMS[shim])
                print(f"Copying {shim_source_path} -> {shim_destination_path}")
                ida_shim_data = pkgutil.get_data('ilstrap', shim_source_path)
                assert ida_shim_data

                ida_shim.write(ida_shim_data)

        for ida_module in IDA_MODULES:
            ida_module_destination = path.join(self.install_path, ida_module)
            print(f"Copying {ida_module} -> {ida_module_destination}")
            with open(ida_module_destination, 'wb') as ida_module_file:
                ida_module_data = pkgutil.get_data('ilstrap', ida_module)
                assert ida_module_data

                ida_module_file.write(ida_module_data)

    def install(self, project: IStrapProject, dev_mode=False):
        assert self.configuration

        if dev_mode:
            project.link_to(self.install_path)
        else:
            project.copy_to(self.install_path)

        self.configuration.packages[project.name] = project.source_path
        self.save_configuration()


def main():
    parser = argparse.ArgumentParser(description='Configure IDA and IDAPython for a istrap project')
    parser.add_argument('project_path', type=str, nargs='?', default=os.curdir,
                        help='the location of the project, where istrap.json is (uses cwd by default)')
    parser.add_argument('--gh', dest='repo_url', type=str, default=None,
                        help="location of the istrap_plugin.py to use (uses ilstrap version by default)")
    parser.add_argument('--ida', dest='ida_path', type=str, default=IDA.guess_ida_install_dir(),
                        help="location of the ida install (will ask interactively with a guess by default)")
    parser.add_argument('--dev_mode', action='store_true')
    parser.set_defaults(dev_mode=False)

    args = parser.parse_args()
    args.project_path = path.realpath(args.project_path)
    if args.ida_path:
        args.ida_path = path.realpath(args.ida_path)

    if sys.platform == 'win32' and not Windows.is_admin():
        print('On Windows, this script needs to be ran from an administrator command prompt')
        exit(1)

    if not args.ida_path:
        if platform in ["darwin", "linux", "linux2"]:
            args.ida_path = input(f'Enter IDA Install Location \n> ')

        elif platform == "win32":
            args.ida_path = Windows.get_path()

        else:
            print('Unknown OS')
            exit(2)

    if not IDA.is_ida_path(args.ida_path):
        print(f'Path {args.ida_path} is not is not IDA install directory!')
        exit(1)

    print(f'Got IDA Install: {args.ida_path}')
    ida = IDA(args.ida_path)

    print('Copying istrap bootstrapper')
    ida.install_istrap()

    if args.dev_mode:
        print('Will install with dev_mode')

    if args.repo_url:
        project = IStrapProject.from_repo(args.repo_url)
    else:
        if not IStrapProject.is_project_path(args.project_path):
            print(f"Unable to find istrap.json in {args.project_path}")
            exit(1)

        project = IStrapProject.from_project_path(args.project_path)

    with project:
        ida.install(project, dev_mode=args.dev_mode)

    print('Finished.')


if __name__ == "__main__":
    main()
