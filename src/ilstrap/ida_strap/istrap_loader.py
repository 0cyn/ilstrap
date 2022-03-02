import sys
import typing
from os import path

import idaapi


IDA_REJECT_FILE = 0

LOADER_ROOT = path.dirname(__file__)
PLUGIN_ROOT = path.realpath(path.join(LOADER_ROOT, '..', 'plugins'))
ISTRAP_ROOT = path.join(PLUGIN_ROOT, 'ilstrap')
LOCAL_CONFIG = path.join(ISTRAP_ROOT, 'istrap.json')

print('[ilstraploader] begin loader shim...')

if PLUGIN_ROOT not in sys.path:
    sys.path.insert(0, PLUGIN_ROOT)


idaapi.load_plugin(path.realpath(path.join(PLUGIN_ROOT, 'istrap_plugin.py')))

import ilstrap.environment

ENVIRONMENT = ilstrap.environment.IStrapEnvironment.environment()

ENVIRONMENT.prepare_load_path()
ENVIRONMENT.prepare_loaders()


def accept_file(file_descriptor, file_name: str):
    for loader_name in ENVIRONMENT.loaders:
        loader = ENVIRONMENT.get_loader(loader_name)
        print(f"Testing loader {loader.name} for file {file_name}")
        result = loader.accept_file(file_descriptor, file_name)

        if not result == IDA_REJECT_FILE:
            print(f"Loader {loader.name} accepted file")
            ENVIRONMENT.set_loader(result['format'], loader)
            return result

    return IDA_REJECT_FILE


def load_file(file_descriptor, neflags, file_format):
    print(f"loading with flags {neflags}, with format {file_format}")
    loader = ENVIRONMENT.get_for_format(file_format)
    return loader.load_file(file_descriptor, neflags, file_format)
