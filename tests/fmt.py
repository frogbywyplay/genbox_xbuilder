# Copyright (C) 2006-2018 Wyplay, All Rights Reserved.
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

import subprocess
import sys
import os


def _find_py():
    r""" find -name \*.py """
    for root, _, files in os.walk('.'):
        for fname in files:
            if os.path.splitext(fname)[1] == '.py':
                yield os.path.join(root, fname)


def fmt():
    print('* running unify')
    unify_stdout = subprocess.check_output(['unify', '-r', '.']).strip()
    if unify_stdout:
        print(unify_stdout)
        yield 1
    print('* running yapf')

    p = subprocess.Popen(['yapf', '-d'] + list(_find_py()), stdout=subprocess.PIPE)
    yapf_stdout, _ = p.communicate()
    if p.returncode:
        print(yapf_stdout)
        yield 1


def main():
    err = sum(fmt())
    if err:
        print('You can run `python setup.py fmt` to fix this')
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
