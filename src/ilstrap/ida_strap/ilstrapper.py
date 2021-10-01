from os import path, listdir
import sys

"""
Structure:

IDA Pro *.*/
  ...
  loaders/
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
    # figure out where ilstrap/ is
    ilstrap_dir = this_dir + path.sep + "ilstrap" + path.sep + name
    sys.path.insert(0, ilstrap_dir)