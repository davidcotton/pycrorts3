from setuptools import setup, find_packages

setup(
    name='pycrorts3',
    version='0.1.0',
    description='PycroRTS 3',
    long_description=open('README.md').read(),
    install_requires=['gym>=0.10.3', 'ray[rllib, debug]', 'untangle'],
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    package_data={'pycrorts3': ['game/maps/*.xml']},
)
