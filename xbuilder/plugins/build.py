#!/usr/bin/python
#
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
#
#

import os
import readline

from subprocess import Popen, PIPE

from xutils import XUtilsError
from xutils.ebuild import ebuild_factory

from xtarget import XTargetError

from xbuilder.archive import Archive
from xbuilder.plugin import XBuilderPlugin

BUILD_LOG_BUFSIZE = 1024 * 1024 * 2 # 2Mo should be enough

class XBuilderBuildPlugin(XBuilderPlugin):
        def build(self, target_ebuild, target_builder, arch=None):
                """ Build a target filesystem using the given target ebuild """
                if not target_ebuild.endswith('.ebuild'):
                        target_ebuild = target_builder.xportage.best_match(target_ebuild)
                        target_ebuild = target_builder.xportage.portdb.findname(target_ebuild)

                ebuild = ebuild_factory(target_ebuild)
                eb_cpv = ebuild.get_cpv()
                self.info('Building %s' % eb_cpv)

                workdir = self.cfg['build']['workdir']

                try:
                        self.log_fd.flush()
                        target_builder.create('=%s' % eb_cpv, arch, workdir)
                        target_builder.set(workdir)
                        target_builder.sync_overlay(workdir)
                except XTargetError, e:
                        raise XUtilsError(error=str(e))

                env = os.environ.copy()

		if "MAKEOPTS" not in env:
			env["MAKEOPTS"] = "-j"+str(os.sysconf('SC_NPROCESSORS_ONLN'))

		if 'distcc' in self.cfg['build']['features']:
		    distccopts = Popen(["/usr/bin/distcc", "-j"], stdout=PIPE)
		    makeopts = "-j"+distccopts.stdout.readline().strip()
		    env.update({'MAKEOPTS'              : makeopts})


                env.update({
                            'PORTAGE_ELOG_CLASSES'  : 'warn error qa',
                            'PORTAGE_ELOG_SYSTEM'   : 'save',
                            'FEATURES'              : self.cfg['build']['features']
                           })

                self.log_fd.flush()
                ret = Popen(["xmerge", "-uvND", "world"], bufsize=BUILD_LOG_BUFSIZE,
                            stdout=self.log_fd, stderr=self.log_fd, shell=False,
                            env=env,
                            cwd=None).wait()
                if ret != 0:
                        raise XUtilsError("Target build failed, please see the log file %s" % self.log_file)

        def release(self, build_info):
                if not build_info['success']:
                        self.info('Build failure: nothing to copy on %s' % self.cfg['release']['server'])
                        return

                src_dir = self.cfg['build']['workdir']
                files = [
                    '%s-%s_root.tar.%s' % (build_info['pkg_name'], build_info['version'], self.cfg['release']['compression']),
                    '%s-%s_debuginfo.tar.%s' % (build_info['pkg_name'], build_info['version'], self.cfg['release']['compression']),
                ]
                for f in os.listdir(self.cfg['build']['workdir']):
                        if f.endswith('_root.tar.%s.gpg' % self.cfg['release']['compression']):
                                files = map(lambda x: '%s/%s.gpg' % (src_dir, x), files)
                                break
                        elif f.endswith('_root.tar.%s' % self.cfg['release']['compression']):
                                files = map(lambda x: '%s/%s' % (src_dir, x), files)
                                break
                destination = '/'.join([self.cfg['release']['basedir'], build_info['category'],
                        build_info['pkg_name'], build_info['version'], build_info['arch']])

                self.info('Uploading prebuilt to %s' % self.cfg['release']['server'])
                archive = Archive(self.cfg['release']['server'])
                archive.upload(files, destination)


def register(builder):
        builder.add_plugin(XBuilderBuildPlugin)

