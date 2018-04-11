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

import os
import re

from portage import config, create_trees  # pylint: disable=no-name-in-module
from portage.exception import InvalidAtom
from portage.versions import catpkgsplit, pkgsplit

from xbuilder.plugin import XBuilderPlugin


class XBuilderAnalyzerPlugin(XBuilderPlugin):
    @staticmethod
    def validateLogfile(package, config_, target):  # pylint: disable=too-many-locals
        try:
            my_root = os.path.join('/usr/targets', os.getenv('CURRENT_TARGET', target), 'root/')
            my_trees = create_trees(config_root=my_root, target_root=my_root)
            portage_db = my_trees[my_root]['vartree'].dbapi
            [cpv] = portage_db.match(package)
        except (InvalidAtom, ValueError):
            return None

        if not cpv:
            return None

        [license_] = portage_db.aux_get(cpv, ['LICENSE'])
        if license_.lower() != 'wyplay':
            return None

        category, name, version, revision = catpkgsplit(cpv)
        logfile = '%s:%s-%s%s:' % (category, name, version, str() if revision == 'r0' else '-%s' % revision)
        try:
            file_ = next(fname for fname in os.listdir(config_['PORT_LOGDIR']) if fname.startswith(logfile))
        except StopIteration:
            return None

        filepath = os.path.abspath(os.path.join(config_['PORT_LOGDIR'], file_))
        with open(filepath, 'r') as fd:
            compiler_pattern = r'^\s?%s-g' % config_['CHOST']
            try:
                line = next(l for l in fd if re.match(compiler_pattern, l))
            except StopIteration:
                return None

        return list(v for k, v in [(' -Wall ', 'NO_WALL'), (' -Wextra ', 'NO_WEXTRA')] if k not in line)

    def postbuild_success(self, build_info):
        """ Analyze compilation logs
        """
        statusdict = dict(NO_WALL=list(), NO_WEXTRA=list())

        target = os.path.join(
            '/usr/targets', os.getenv('CURRENT_TARGET', os.path.basename(self.cfg['build']['workdir'])), 'root'
        )
        myconfig = config(target_root=target, config_root=target)
        for item in myconfig.packages:
            if item.startswith('*'):
                continue
            cp, v, r = pkgsplit(item[1:])
            noflags = self.validateLogfile(cp, myconfig, os.path.basename(self.cfg['build']['workdir']))
            if noflags:
                s = '%s-%s%s' % (cp, v, '-%s' % r if r != 'r0' else '')
                for k in noflags:
                    statusdict[k].append(s)

        report = ['#. Log file analysis report\n\n']
        if statusdict['NO_WALL']:
            report.append(
                "Packages which do not have '-Wall' compiler flag enabled:\n\n" +
                ''.join('\t* %s\n' % s for s in statusdict['NO_WALL'])
            )
        if statusdict['NO_WEXTRA']:
            report.append(
                "Packages which do not have '-Wextra' compiler flag enabled:\n\n" +
                ''.join('\t* %s\n' % s for s in statusdict['NO_WEXTRA'])
            )
        if len(report) == 1:
            report.append('Congratulations: everything is perfect!')
        build_info['analyzer'] = ''.join(report)


def register(builder):  # pragma: no cover
    builder.add_plugin(XBuilderAnalyzerPlugin)
