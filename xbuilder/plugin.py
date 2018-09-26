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

class XBuilderPlugin(object):
        def __init__(self, cfg, info, log_fd, log_file):
                self.cfg = cfg
                self.info = info
                self.log_fd = log_fd
                self.log_file = log_file

        def prebuild(self, target_ebuild, arch=None):
                pass
        def build(self, target_ebuild, target_builder, arch=None):
                pass
        def postbuild(self, build_info):
                pass
        def release(self, build_info):
                pass

