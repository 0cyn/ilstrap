from setuptools import setup

setup(name='ilstrap',
      version='0.1.0',
      description='IDA Loader Installer',
      long_description='file: README.md',
      long_description_content_type='text/markdown',
      author='kritanta',
      url='https://github.com/kritantadev/ilstrap',
      install_requires=[],
      packages=['ilstrap'],
      package_dir={
            'ilstrap': 'src/ilstrap',
      },
      package_data={
          'ilstrap': ['sys_scripts/*', 'ida_strap/*'],
      },
      classifiers=[
            'Programming Language :: Python :: 3',
            'License :: OSI Approved :: MIT License',
            'Operating System :: OS Independent'
      ]
      )
