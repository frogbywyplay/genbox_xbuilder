#!/usr/bin/python
#
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
#
#

from __future__ import absolute_import

import argparse

from xutils import die, XUtilsError

from xbuilder.consts import XBUILDER_DEFTYPE
from xbuilder.builder import XBuilder


class MultiOption(argparse.Action):  # pylint: disable=too-few-public-methods
    def __call__(self, parser, namespace, values, option_string=None):
        items = values.split(',')
        setattr(namespace, self.dest, items)


def make_parser():
    parser = argparse.ArgumentParser(description='Builder tool for genbox-ng.')
    parser.register('action', 'multi_store', MultiOption)
    parser.add_argument(
        '--ov-rev',
        action='multi_store',
        help='Fix an overlay revision (syntax: "ov:rev[,ov:rev...]").',
        default=list()
    )
    parser.add_argument('-r', '--rev', help='Fix profile revision.')
    parser.add_argument(
        '-t', '--type', help='Set the type of build: beta (default) or release.', default=XBUILDER_DEFTYPE
    )
    parser.add_argument('-c', '--config', help='Use an alternate config file.')
    parser.add_argument('-a', '--arch', help='Specify the target arch to build.')
    parser.add_argument('--as', dest='user_version', help="Use user ebuild's name")
    parser.add_argument('pkg_atom', help='target package atom')
    return parser


def main():
    parser = make_parser()
    args = parser.parse_args()

    try:
        builder = XBuilder(args.config, args.type)
    except XUtilsError as e:
        die(str(e))

    rev = (args.rev, dict(ov.split(':') for ov in args.ov_rev))

    if args.user_version:
        user_version = 'user:%s' % args.user_version
    else:
        user_version = None

    try:
        return not builder.run(args.pkg_atom, rev, args.arch, name=user_version)
    except XUtilsError as e:
        builder.cleanup()
        die(str(e))
