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

import os
from os.path import exists

from shutil import copy

from xbuilder.plugin import XBuilderPlugin



class XBuilderXversionPlugin(XBuilderPlugin):

        def postbuild(self, build_info):
                self.info('Filling version in /etc/version')
                rootdir = self.cfg['build']['workdir'] + '/root'
		redistdir = rootdir + '/redist'
		versionfile = rootdir + '/etc/' + os.path.dirname(os.readlink(rootdir + '/etc/portage/make.profile')) + '/version'

		if exists(versionfile):
			copy(versionfile, rootdir + '/etc')
			copy(versionfile, redistdir + '/etc')

		fd = open(rootdir + '/etc/version', 'a')
		fd.write( build_info['version'] + '\n')
                fd.close()

		fd = open(redistdir + '/etc/version', 'a')
		fd.write( build_info['version'] + '\n' )
                fd.close()

def register(builder):
        builder.add_plugin(XBuilderXversionPlugin)

