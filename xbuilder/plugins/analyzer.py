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

from os import getenv, listdir
from os.path import abspath, basename
from re import match, IGNORECASE
from xbuilder.plugin import XBuilderPlugin
from xintegtools.xchecker import Ebuild, ProfileParser, validateEbuild, validateProfile, InvalidArgument

OK = 0
NO_WALL = 1
NO_WEXTRA = 2
SKIPPED = 4

def validateLogfile(package, config):
    status = OK
    try:
        myebuild = Ebuild(package)
    except InvalidArgument:
        status = SKIPPED
        return status


    if not match('^wyplay$', myebuild.license, IGNORECASE):
        status = SKIPPED
        return status

    logfile = '%s:%s-%s%s:' % (myebuild.category, myebuild.name, myebuild.version, str() if myebuild.revision == 0 else "-r%d" % myebuild.revision)
    for file in listdir(config['PORT_LOGDIR']):
        if file.startswith(logfile):
            filepath = abspath('%s/%s' % (config['PORT_LOGDIR'], file))
            fd = open(filepath, 'r')
            for line in fd.readlines():
                compiler_pattern = '^\s?%s-g' % config['CHOST']
                if match(compiler_pattern, line):
                    if not ' -Wall ' in line:
                        status += NO_WALL
                    if not ' -Wextra ' in line:
                        status += NO_WEXTRA
                    break
            fd.close()
            break
    return status

class XBuilderAnalyzerPlugin(XBuilderPlugin):

    def postbuild(self, build_info):
        """ Analyze compilation logs
        """
        analyze = '## Log file analysis report\n\n'
        statusdict = {OK: list(), NO_WALL: list(), NO_WEXTRA: list(), NO_WALL + NO_WEXTRA: list(), SKIPPED: list()}

        if not build_info['success']:
            return

        target = getenv('CURRENT_TARGET', basename(self.cfg['build']['workdir']))
        profile = ProfileParser(target)
        for package in profile.packages.keys():
            status = validateLogfile(package, profile.profile_config)
            statusdict[status] += ['%s-%s' % (package, profile.packages[package])]

        build_info['analyzer'] =  analyze
        if len(statusdict[NO_WALL] + statusdict[NO_WALL + NO_WEXTRA]) > 0:
            build_info['analyzer'] +=  'Packages which do not have \'-Wall\' compiler flag enabled:\n\n'
            for s in statusdict[NO_WALL] + statusdict[NO_WALL + NO_WEXTRA]:
                build_info['analyzer'] += '\t* %s\n' % s
        if len(statusdict[NO_WEXTRA] + statusdict[NO_WALL + NO_WEXTRA]) > 0:
            build_info['analyzer'] +=  'Packages which do not have \'-Wextra\' compiler flag enabled:\n\n'
            for s in statusdict[NO_WEXTRA] + statusdict[NO_WALL + NO_WEXTRA]:
                build_info['analyzer'] += '\t* %s\n' % s
        if build_info['analyzer'] == analyze:
            build_info['analyzer'] += 'Congratulations: everything is perfect!'

def register(builder):
    builder.add_plugin(XBuilderAnalyzerPlugin)

