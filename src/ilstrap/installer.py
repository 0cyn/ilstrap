import argparse
import dataclasses
import json
import os
import random
import re
import shutil
import string
import sys
import pkgutil
import tarfile
import tempfile
import typing
from os import path, listdir
from sys import platform
from urllib import request

from .windows import Windows
from .shared import *

DARWIN_APPLICATIONS = "/Applications"
DARWIN_IDA_INSTALL = re.compile(r"^IDA Pro \d+\.\d+")
GITHUB_REPO_PATTERN = re.compile(r"(\w+)/(\w+)")


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

        istraper = pkgutil.get_data('ilstrap', 'ida_strap/istrapper.py')
        assert istraper

        common_data = pkgutil.get_data('ilstrap', 'shared.py')
        assert common_data

        with open(path.join(self.ida_dir('plugins'), f'istrapper.py'), 'wb') as output_istrapper:
            output_istrapper.write(istraper)

        with open(path.join(self.install_path, '__init__.py'), 'w') as module_marker:
            module_marker.write(str())

        with open(path.join(self.install_path, 'shared.py'), 'wb') as common_file:
            common_file.write(common_data)

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
                        help="location of the istrapper.py to use (uses ilstrap version by default)")
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
