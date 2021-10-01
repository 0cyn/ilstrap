import os.path as path


def get_package_filepath(dir, filename):

    return path.dirname(__file__) + f'/{dir}/' + filename

