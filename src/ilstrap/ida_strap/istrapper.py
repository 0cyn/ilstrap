from os import path, listdir
import sys

import idaapi
import ida_hexrays

"""
Structure:

IDA Pro *.*/
  ...
  loaders/ (or plugins/)
    ilstrap/
      some_loader_name/
        module1/
        module2/
        module3/
    ilstrapper.py <- WE ARE HERE
    some_loader.py
  ...

"""


def loadmods(name):
    # get the dir this actual ilstrap.py script is running in
    this_dir = path.dirname(__file__)
    # figure out where istrap/ is
    ilstrap_dir = this_dir + path.sep + "istrap" + path.sep + name
    sys.path.insert(0, ilstrap_dir)

# since IDA expects every file here to be an IDA Loader, conform to that API to avoid errors
def accept_file(fd, fname):
    return 0

# same for plugins, we use this file for both


class IStrapPlugin(idaapi.plugin_t):
    flags = idaapi.PLUGIN_PROC | idaapi.PLUGIN_HIDE
    comment = "IStrap Plugin"
    wanted_hotkey = ""
    help = "Runs transparently"
    wanted_name = "IStrap Plugin"
    hook = None
    enabled = 1

    def init(self):
        return idaapi.PLUGIN_KEEP

    def run():
        pass

    def term(self):
        pass

def PLUGIN_ENTRY():
    return IStrapPlugin()
