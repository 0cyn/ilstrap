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
        self.plugins_dir = self.path + path.sep + 'plugins'

    def get_data(self):
        # We will eventually use this for update checks
        # I think i'll need to add an istrap 'plugin' to make that happen without being a PITA to do though
        if path.isdir(self.loaders_dir + path.sep + 'istrap'):
            if path.isfile(self.loaders_dir + path.sep + 'istrap' + path.sep + 'istrap.json'):
                with open(self.loaders_dir + path.sep + 'istrap' + path.sep + 'istrap.json', 'r') as fp:
                    return json.load(fp)
        # This is the default data dict created when none exists
        return {
            'comment': 'This is where istrap saves info about installed modules',
            'version': 2,
            'loaders': {},
            'plugins': {}
        }

    def save_data(self, data):
        with open(self.loaders_dir + path.sep + 'istrap' + path.sep + 'istrap.json', 'w') as fp:
            json.dump(data, fp)

    def confirm_is_ida(self):
        # print(f'Path {self.path + path.sep + "ida64.exe"}: {path.isfile(self.path + path.sep + "ida64.exe")}')
        # I think this should account for installing from WSL1?
        # why on earth would one do that, though ;_;
        return path.isfile(self.path + path.sep + 'ida64.exe') or path.isfile(self.path + path.sep + 'ida64')

    def install_istrap(self):
        # do this every time so it's possible to softly push updates to it
        istrap_fn = get_package_filepath('ida_strap', 'istrapper.py')
        shutil.copy(istrap_fn, self.loaders_dir + path.sep + 'ilstrapper.py')

        istrap_dir_name = self.loaders_dir + path.sep + 'istrap'

        if not path.isdir(istrap_dir_name):
            os.mkdir(istrap_dir_name)

        # do this every time so it's possible to softly push updates to it
        istrap_fn = get_package_filepath('ida_strap', 'istrapper.py')
        shutil.copy(istrap_fn, self.plugins_dir + path.sep + 'ipstrapper.py')

        istrap_dir_name = self.plugins_dir + path.sep + 'istrap'

        if not path.isdir(istrap_dir_name):
            os.mkdir(istrap_dir_name)

    @staticmethod
    def get_gh_repo_tarball(given):
        url = f'https://api.github.com/repos/{given}/releases/latest'
        response: dict = json.load(request.urlopen(url))
        tar_url = response['tarball_url']
        return tar_url

    def install_from_local_dir(self, outpath):

        config = None

        with open(outpath + path.sep + 'istrap.json') as conf:
            config = json.load(conf)

        modname = config['name']

        if 'loader-modules' in config:
            modsdir = config['loader-modules']
        else:
            modsdir = None
        ldrname = config['loader']

        istrap_data = self.get_data()
        istrap_data['loaders'][modname] = config
        self.save_data(istrap_data)

        packpath = path.join(self.loaders_dir + path.sep + 'istrap', modname)

        if not path.exists(packpath):
            os.mkdir(packpath)

        shutil.copy(outpath + path.sep + ldrname, self.loaders_dir)

        # prepend the istrap load info into the loader

        ldrname = os.path.basename(ldrname)

        loader_loc = path.join(self.loaders_dir, ldrname)

        if modsdir:
            line_prepender(loader_loc, f'ilstrapper.loadmods(\'{modname}\')')

        line_prepender(loader_loc, 'import ilstrapper')

        if modsdir:
            for modulename in listdir(outpath + path.sep + modsdir):
                mod_fqp = path.join(outpath + path.sep + modsdir, modulename)
                mod_outdir = path.join(packpath, modulename)
                if not path.exists(mod_outdir):
                    os.mkdir(mod_outdir)
                for fn in listdir(mod_fqp):
                    file_fqp = path.join(mod_fqp, fn)
                    shutil.copyfile(file_fqp, mod_outdir + path.sep + fn)


        # plugin

        if 'plugin-modules' in config:
            modsdir = config['plugin-modules']
        else:
            modsdir = None
        ldrname = config['plugin']

        istrap_data = self.get_data()
        istrap_data['plugins'][modname] = config
        self.save_data(istrap_data)

        packpath = path.join(self.plugins_dir + path.sep + 'istrap', modname)

        if not path.exists(packpath):
            os.mkdir(packpath)

        shutil.copy(outpath + path.sep + ldrname, self.plugins_dir)

        ldrname = os.path.basename(ldrname)

        # prepend the istrap load info into the loader
        loader_loc = path.join(self.plugins_dir, ldrname)

        if modsdir:
            line_prepender(loader_loc, f'ipstrapper.loadmods(\'{modname}\')')

        line_prepender(loader_loc, 'import ipstrapper')

        if modsdir:
            for modulename in listdir(outpath + path.sep + modsdir):
                mod_fqp = path.join(outpath + path.sep + modsdir, modulename)
                mod_outdir = path.join(packpath, modulename)
                if not path.exists(mod_outdir):
                    os.mkdir(mod_outdir)
                for fn in listdir(mod_fqp):
                    file_fqp = path.join(mod_fqp, fn)
                    shutil.copyfile(file_fqp, mod_outdir + path.sep + fn)


    def install_loader_from_url_tarball(self, url):
        response = requests.get(url, stream=True)
        file = tarfile.open(fileobj=response.raw, mode="r|gz")
        outpath = tempfile.gettempdir() + path.sep + 'istrap_loader_install.' + ''.join(
            random.choice(string.ascii_lowercase) for i in range(10))
        file.extractall(path=outpath)
        # iterate the files in that directory
        
        for filename in listdir(outpath):
            fqp = path.join(outpath, filename)
            if 'istrap.json' in listdir(fqp):
                self.install_from_local_dir(fqp)
                break
        # os.remove(outpath)

def main():

    local = False

    tar_url = ''

    cd = os.getcwd()

    if len(sys.argv) < 2:
        local = True
        print(f'Installing from current dir ({cd})')
    else:
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
    print('Copying istrap bootstrapper')
    ida.install_istrap()
    print('Installing Loader')
    if local:
        ida.install_from_local_dir(cd)
    else:
        ida.install_loader_from_url_tarball(tar_url)
    print('Finished.')

if __name__ == "__main__":
    main()
