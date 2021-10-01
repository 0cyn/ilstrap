from sys import platform
from .windows import Windows
from os import path, listdir
import sys
import os
from .shared import get_package_filepath
import requests
from urllib import request
import tarfile
import tempfile
import shutil
import json
import string
import random


def line_prepender(filename, line):
    with open(filename, 'r+') as f:
        content = f.read()
        f.seek(0, 0)
        f.write(line.rstrip('\r\n') + '\n' + content)


class IDA:
    def __init__(self, pathnam):
        self.path = pathnam
        self.loaders_dir = self.path + path.sep + 'loaders'

    def get_data(self):
        # We will eventually use this for update checks
        # I think i'll need to add an ilstrap 'plugin' to make that happen without being a PITA to do though
        if path.isdir(self.loaders_dir + path.sep + 'ilstrap'):
            if path.isfile(self.loaders_dir + path.sep + 'ilstrap' + path.sep + 'ilstrap.json'):
                with open(self.loaders_dir + path.sep + 'ilstrap' + path.sep + 'ilstrap.json', 'r') as fp:
                    return json.load(fp)
        # This is the default data dict created when none exists
        return {
            'comment': 'This is where ILStrap saves info about installed modules',
            'version': 1,
            'loaders': {}
        }

    def save_data(self, data):
        with open(self.loaders_dir + path.sep + 'ilstrap' + path.sep + 'ilstrap.json', 'w') as fp:
            json.dump(data, fp)

    def confirm_is_ida(self):
        # print(f'Path {self.path + path.sep + "ida64.exe"}: {path.isfile(self.path + path.sep + "ida64.exe")}')
        # I think this should account for installing from WSL1?
        # why on earth would one do that, though ;_;
        return path.isfile(self.path + path.sep + 'ida64.exe') or path.isfile(self.path + path.sep + 'ida64')

    def install_ilstrap(self):
        # do this every time so it's possible to softly push updates to it
        ilstrap_fn = get_package_filepath('ida_strap', 'ilstrapper.py')
        shutil.copy(ilstrap_fn, self.loaders_dir + path.sep + 'ilstrapper.py')

        ilstrap_dir_name = self.loaders_dir + path.sep + 'ilstrap'

        if not path.isdir(ilstrap_dir_name):
            os.mkdir(ilstrap_dir_name)

    @staticmethod
    def get_gh_repo_tarball(given):
        url = f'https://api.github.com/repos/{given}/releases/latest'
        response: dict = json.load(request.urlopen(url))
        tar_url = response['tarball_url']
        return tar_url

    def install_loader_from_url_tarball(self, url):
        response = requests.get(url, stream=True)
        file = tarfile.open(fileobj=response.raw, mode="r|gz")
        outpath = tempfile.gettempdir() + path.sep + 'ilstrap_loader_install.' + ''.join(
            random.choice(string.ascii_lowercase) for i in range(10))
        file.extractall(path=outpath)
        # iterate the files in that directory
        for filename in listdir(outpath):
            # IDK if this actually occurs in python on UNIX systems but better safe than sorry /shrug
            if filename == '.' or filename == '..' or filename == '.DS_Store':
                continue

            fully_qualified_pathname = path.join(outpath, filename)
            config = None

            with open(fully_qualified_pathname + path.sep + 'ilstrap.json') as conf:
                config = json.load(conf)

            modname = config['name']
            if 'modules' in config:
                modsdir = config['modules']
            else:
                modsdir = None
            ldrname = config['loader']

            ilstrap_data = self.get_data()
            ilstrap_data['loaders'][modname] = config
            self.save_data(ilstrap_data)

            packpath = path.join(self.loaders_dir + path.sep + 'ilstrap', modname)

            if not path.exists(packpath):
                os.mkdir(packpath)

            shutil.copy(fully_qualified_pathname + path.sep + ldrname, self.loaders_dir)

            # prepend the ilstrap load info into the loader
            loader_loc = path.join(self.loaders_dir, ldrname)

            if modsdir:
                line_prepender(loader_loc, f'ilstrapper.loadmods(\'{modname}\')')

            line_prepender(loader_loc, 'import ilstrapper')

            if modsdir:
                for modulename in listdir(fully_qualified_pathname + path.sep + modsdir):
                    mod_fqp = path.join(fully_qualified_pathname + path.sep + modsdir, modulename)
                    mod_outdir = path.join(packpath, modulename)
                    if not path.exists(mod_outdir):
                        os.mkdir(mod_outdir)
                    for fn in listdir(mod_fqp):
                        file_fqp = path.join(mod_fqp, fn)
                        shutil.copyfile(file_fqp, mod_outdir + path.sep + fn)

        # why cant we do this?
        # os.remove(outpath)


def main():
    tar_url = sys.argv[1]
    if sys.argv[1] == '--gh':
        gh = sys.argv[2]
        tar_url = IDA.get_gh_repo_tarball(gh)
        print('Successfully found repo')

    if platform == "linux" or platform == "linux2":
        pathname = input('Enter IDA Install Location \n> ')
    elif platform == "darwin":
        pathname = input('Enter IDA Install Location \n> ')
    elif platform == "win32":
        if not Windows.is_admin():
            print('On Windows, this script needs to be ran from an administrator command prompt')
            exit(1)
        pathname = Windows.get_path()
    else:
        pathname = None

        print('Unknown OS')
        exit(2)

    ida = IDA(pathname)

    if not ida.confirm_is_ida():
        print('Path is not is not IDA install directory!')
        exit(1)
    print('Got IDA Dir')
    print('Copying ILStrap bootstrapper')
    ida.install_ilstrap()
    print('Installing Loader')
    ida.install_loader_from_url_tarball(tar_url)
    print('Finished.')

if __name__ == "__main__":
    main()
