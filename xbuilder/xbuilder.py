#!/usr/bin/python
#
# Copyright (C) 2006-2014 Wyplay, All Rights Reserved.
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

import sys

from optparse import OptionParser, Option

from xutils import die, XUtilsError

from xbuilder.consts import XBUILDER_DEFTYPE
from xbuilder.builder import XBuilder


class MultiOption(Option):
    ACTIONS = Option.ACTIONS + ('multi_store', )
    STORE_ACTIONS = Option.STORE_ACTIONS + ('multi_store', )
    TYPED_ACTIONS = Option.TYPED_ACTIONS + ('multi_store', )
    ALWAYS_TYPED_ACTIONS = Option.ALWAYS_TYPED_ACTIONS + ('multi_store', )

    def take_action(self, action, dest, opt, value, values, parser):  # pylint: disable=too-many-arguments
        if action == 'multi_store':
            lvalue = value.split(',')
            values.ensure_value(dest, []).extend(lvalue)
        else:
            Option.take_action(self, action, dest, opt, value, values, parser)


options = [
    MultiOption(
        None,
        '--ov-rev',
        action='multi_store',
        dest='ov_list',
        help='Fix an overlay revision (syntax: "ov:rev[,ov:rev...]").'
    ),
    Option('-r', '--rev', action='store', dest='profile_rev', help='Fix profile revision.'),
    Option('-t', '--type', action='store', dest='build_type', help='Set the type of build: beta (default) or release.'),
    Option('-c', '--config', action='store', dest='config', help='Use an alternate config file.'),
    Option('-a', '--arch', action='store', dest='arch', help='Specify the target arch to build.'),
    Option(None, '--as', action='store', dest='user_version', help="Use user ebuild's name"),
    #Option(None, '--autobump', action='store', dest='autobump', help='Bump every package matching the regexp.'),
]


def main():
    parser = OptionParser(
        usage='%prog [options] pkg_atom', description='Builder tool for genbox-ng.', option_list=options
    )

    values, args = parser.parse_args()

    try:
        pkg_atom, = args
    except ValueError:
        parser.error('a target pkg_atom is required')

    config = values.ensure_value('config', None)
    type_ = values.ensure_value('type', XBUILDER_DEFTYPE)

    try:
        builder = XBuilder(config, type_)
    except XUtilsError as e:
        die(str(e))

    rev = (
        values.ensure_value('profile_rev', str()), dict(ov.split(':') for ov in values.ensure_value('ov_list', list()))
    )

    arch = values.ensure_value('arch', None)
    user_version = None
    if values.ensure_value('user_version', None):
        user_version = 'user:%s' % values.user_version

    try:
        success = builder.run(pkg_atom, rev, arch, name=user_version)
        if success:
            sys.exit(0)
        else:
            sys.exit(1)
    except XUtilsError as e:
        builder.cleanup()
        die(str(e))