#!/usr/bin/python2
# Copyright (C) 2006-2019 Wyplay, All Rights Reserved.
# This file is part of xbuilder.
#
# xbuilder is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
#
# xbuilder is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; see file COPYING.
# If not, see <http://www.gnu.org/licenses/>.

from __future__ import print_function

import contextlib
import glob
import os
import subprocess
import sys
from unittest import TextTestRunner, TestLoader

from setuptools import setup, Command

try:
    import coverage

    @contextlib.contextmanager
    def cov(packages):
        def report_list_aux():
            for package in packages:
                for root, _, files in os.walk(package):
                    for fname in files:
                        if fname.endswith('.py'):
                            yield os.path.join(root, fname)

        report_list = list(set(report_list_aux()))
        c = coverage.Coverage()
        c.erase()
        c.start()
        yield
        c.stop()
        print('\nCoverage report:')
        c.report(report_list)

except ImportError:
    print("Can't find the coverage module")

    @contextlib.contextmanager
    def cov(_):
        yield


class TestCommand(Command):
    user_options = [('coverage', 'c', 'Enable coverage output')]
    boolean_options = ['coverage']

    def initialize_options(self):
        self.coverage = False  # pylint: disable=attribute-defined-outside-init

    def finalize_options(self):
        pass

    def run(self):
        '''
        Finds all the tests modules in tests/, and runs them.
        '''

        testfiles = [
            '.'.join(['tests', os.path.splitext(os.path.basename(t))[0]])
            for t in glob.glob(os.path.join('tests', '*.py')) if not t.endswith('__init__.py')
        ]

        with cov(self.distribution.packages):
            tests = TestLoader().loadTestsFromNames(testfiles)
            t = TextTestRunner(verbosity=1)
            ts = t.run(tests)

        if not ts.wasSuccessful():
            sys.exit(1)


class FmtCommand(Command):
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    @staticmethod
    def _find_py():
        r""" find -name \*.py """
        for root, _, files in os.walk('.'):
            for fname in files:
                if os.path.splitext(fname)[1] == '.py':
                    yield os.path.join(root, fname)

    def run(self):
        print('* running unify')
        subprocess.check_call(['unify', '-i', '-r', '.'])
        print('* running yapf')
        subprocess.check_call(['yapf', '-i'] + list(self._find_py()))


setup(
    name='xbuilder',
    version='2.1.13',
    description='Xbuilder tool for genbox',
    author='Wyplay',
    author_email='noreply@wyplay.com',
    url='http://www.wyplay.com',
    install_requires=[
        'python-gnupg',
        'paramiko',
        'portage',
        'profilechecker',
        'requests',
        'xintegtools',
        'xportage',
        'xutils',
    ],
    packages=['xbuilder', 'xbuilder.plugins'],
    data_files=[('/etc', ['config/xbuilder.conf'])],
    long_description='xbuilder tools for genbox',
    cmdclass={
        'test': TestCommand,
        'fmt': FmtCommand,
    },
    tests_require=['coverage'],
    entry_points={
        'console_scripts': [
            'xbuilder = xbuilder.xbuilder:main',
        ],
    },
)
