from .shared import get_package_filepath
import subprocess
import ctypes, sys

class Windows:
    def __init__(self):
        pass

    @staticmethod
    def get_path():
        win_script = get_package_filepath('sys_scripts', 'get_path.bat')
        output = subprocess.Popen(
            (win_script),
            stdout=subprocess.PIPE).stdout
        path_out: bytes = output.read()
        output.close()
        path = path_out.decode('utf-8').strip('\r\n').split(' ', 2)[-1]
        return path

    @staticmethod
    def is_admin():
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            return False
