# -*- encoding: utf-8 -*-
from setuptools import setup, find_packages
import sys
if sys.version_info[0] < 3:
    print("Sorry, Python 2 is not supported.")
    sys.exit(1)

setup(
    name = 'configure.py',
    version = '1.1',
    description = "Configure your project's builds in plain Python",
    author = 'Raphaël Londeix',
    author_email = 'raphael.londeix@gmail.com',
    url = 'http://github.com/hotgloupi/configure.py',
    packages = find_packages('src'),
    package_dir = {'': 'src'},
    scripts = ['bin/configure'],
    test_suite = 'configure',
)
