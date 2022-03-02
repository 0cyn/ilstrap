import dataclasses
import json
import os
import os.path as path
import shutil
import tarfile
import tempfile
import typing
from urllib import request


@dataclasses.dataclass
class IStrapProject:
    name: str
    version: str
    load_paths: list[str] = dataclasses.field(default_factory=list)
    loaders: list[str] = dataclasses.field(default_factory=list)
    plugins: list[str] = dataclasses.field(default_factory=list)

    _workdir: typing.Optional[tempfile.TemporaryDirectory] = dataclasses.field(repr=False, default=None)
    _path: typing.Optional[str] = dataclasses.field(repr=False, default=None)

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._workdir:
            self._workdir.cleanup()

    def _ensure_path(self, install_path, overwrite) -> str:
        if not self._path:
            raise FileNotFoundError

        target_path = path.join(install_path, self.name)

        if overwrite and path.exists(target_path):
            if not path.isdir(target_path):
                os.unlink(target_path)
            else:
                shutil.rmtree(target_path)

        return target_path

    def copy_to(self, install_path, overwrite=True):
        target_path = self._ensure_path(install_path, overwrite)

        if not path.isdir(target_path):
            os.mkdir(target_path)

        shutil.copytree(self._path, target_path, dirs_exist_ok=True)

    def link_to(self, install_path, overwrite=True):
        if self._workdir:
            raise NotADirectoryError('Cannot use dev_mode / link_to with a temp dir')

        target_path = self._ensure_path(install_path, overwrite)

        os.symlink(self._path, target_path)

    @property
    def source_path(self):
        return self._path

    @property
    def module_paths(self):
        for module_path in self.load_paths:
            yield path.realpath(path.join(self._path, module_path))

    @staticmethod
    def is_project_path(project_path):
        return path.isfile(path.join(project_path, 'istrap.json'))

    @classmethod
    def from_file(cls, file_path):
        with open(file_path, 'r') as config_file:
            project = IStrapProject(**json.load(config_file))
            project._path = path.dirname(file_path)
            return project

    @classmethod
    def from_project_path(cls, project_path):
        return cls.from_file(path.join(project_path, 'istrap.json'))

    @classmethod
    def from_repo(cls, repo_name):
        url = f'https://api.github.com/repos/{repo_name}/releases/latest'
        repo_releases: dict = json.load(request.urlopen(url))
        release_tarball = repo_releases['tarball_url']

        with request.urlopen(release_tarball) as tarball_stream:
            tarball = tarfile.open(fileobj=tarball_stream, mode="r|gz")

            workdir = tempfile.TemporaryDirectory(prefix='ilstrap_workdir')
            tarball.extractall(path=workdir.name)

            config = cls.from_project_path(workdir.name)
            config._workdir = workdir
            return config


@dataclasses.dataclass
class IStrapConfig:
    comment: str = dataclasses.field(default="This is the configured list of istrap packages")
    version: int = dataclasses.field(default=3)
    packages: dict[str, str] = dataclasses.field(default_factory=dict)

    @classmethod
    def load_from(cls, config_path):
        if path.isfile(config_path):
            with open(config_path, 'r') as config_file:
                return IStrapConfig(**json.load(config_file))

        return IStrapConfig()

    def save(self, config_path):
        with open(config_path, 'w') as config_file:
            json.dump(dataclasses.asdict(self), config_file)


def get_package_filepath(dirname, filename):
    return path.dirname(__file__) + f'{path.sep}{dirname}{path.sep}' + filename
