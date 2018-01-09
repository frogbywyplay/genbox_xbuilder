#!/usr/bin/python
#
# Copyright (C) 2006-2016 Wyplay, All Rights Reserved.
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
#
#

import contextlib
import glob
import os
import sys
from unittest import TextTestRunner, TestLoader

from distutils.core import setup, Command

try:
    import coverage
except ImportError:

    class Coverage(object):
        def erase(self):
            pass

        def start(self):
            pass

        def stop(self):
            pass

        def report(self):
            pass

    coverage = Coverage()

PACKAGES = ['xbuilder', 'xbuilder.plugins']


@contextlib.contextmanager
def testcoverage():
    coverage.erase()
    coverage.start()
    yield
    coverage.stop()
    print "\nCoverage report:"
    coverage.report(list(py for package in PACKAGES for py in glob.glob(os.path.join(package, '*.py'))))


@contextlib.contextmanager
def nocov():
    yield


class TestCommand(Command):
    user_options = [('coverage', 'c', 'Enable coverage output')]
    boolean_options = ['coverage']

    def initialize_options(self):
        self.coverage = False

    def finalize_options(self):
        pass

    def run(self):
        '''
        Finds all the tests modules in tests/, and runs them.
        '''
        if self.coverage:
            cov = testcoverage
        else:
            cov = nocov

        with cov():
            tests = TestLoader().loadTestsFromNames(
                list(path.replace('/', '.').replace('.py', '') for path in glob.glob('tests/[a-z]*.py'))
            )
            runner = TextTestRunner(verbosity=1)
            run = runner.run(tests)

        if not run.wasSuccessful():
            sys.exit(1)


setup(
    name="xbuilder",
    version="2.1.7",
    description="Xbuilder tool for genbox",
    author="Wyplay",
    author_email="noreply@wyplay.com",
    url="http://www.wyplay.com",
    install_requires=['paramiko', 'portage', 'requests'],
    packages=PACKAGES,
    scripts=[
        "scripts/xbuilder",
    ],
    data_files=[('/etc', ['config/xbuilder.conf'])],
    long_description="""xbuilder tools for genbox""",
    cmdclass={
        'test': TestCommand
    }
)
