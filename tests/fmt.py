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
