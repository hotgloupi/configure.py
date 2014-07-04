# -*- encoding: utf-8 -*-
from setuptools import setup, find_packages
from setuptools_behave import behave_test

setup(
    name = 'configure',
    version = 1.0,
    description = 'Configure your project in plain Python',
    author = 'Raphaël Londeix',
    author_email = 'raphael.londeix@gmail.com',
    url = 'http://github.com/hotgloupi/configure.py',
    packages = find_packages('src'),
    package_dir = {'': 'src'},
    scripts = ['bin/configure'],
    test_suite = 'configure',
    # tests_require = ['behave'],
    cmdclass = {
        'behave_test': behave_test
    }
)
