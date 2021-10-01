import os.path as path


def get_package_filepath(dirname, filename):

    return path.dirname(__file__) + f'{path.sep}{dirname}{path.sep}' + filename

