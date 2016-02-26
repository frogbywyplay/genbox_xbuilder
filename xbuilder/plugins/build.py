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
import readline
import portage
from portage.versions import pkgsplit
from os.path import exists, realpath

from subprocess import Popen, PIPE

from xutils import XUtilsError
from xutils.ebuild import ebuild_factory

from xtarget import XTargetError

from xbuilder.plugin import XBuilderPlugin
from profilechecker.checker import ProfileChecker

BUILD_LOG_BUFSIZE = 1024 * 1024 * 2 # 2Mo should be enough

class XBuilderBuildPlugin(XBuilderPlugin):
        def build(self, target_ebuild, target_builder, arch=None):
                """ Build a target filesystem using the given target ebuild """
                if not target_ebuild.endswith('.ebuild'):
                        target_list = portage.portdb.xmatch('match-all', target_ebuild)
                        try:
                            target_ebuild = portage.portdb.findname2(target_list[0])[0]
                        except IndexError:
                            raise XUtilsError('%s does not match any ebuilds' % target_ebuild)

                ebuild = ebuild_factory(target_ebuild)
                eb_cpv = ebuild.get_cpv()
                self.info('Building %s' % eb_cpv)

                workdir = self.cfg['build']['workdir']

                try:
                        self.log_fd.flush()
                        target_builder.create('=%s' % eb_cpv, arch, workdir)
                except XTargetError, e:
                        raise XUtilsError(error=str(e))

                if self.cfg['build']['enable_profilechecker']:
                    stop_on_warning = self.cfg['profilechecker']['stop_on_warning']
                    stop_on_error = self.cfg['profilechecker']['stop_on_error']

                    checker = ProfileChecker(workdir + '/root', output = self.log_fd)
                    checker.parse()
                    (has_warnings, has_errors) = checker.check_installed_versions()

                    if stop_on_warning and has_warnings:
                        raise XUtilsError('Profile does not meet expected quality requirements. Check %s' % self.log_file)
                    if stop_on_error and has_errors:
                        raise XUtilsError('Some packages will be installed at an unexpected version. Please fix your profile. For more information, check %s' % self.log_file)

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
                ret = Popen(["xmerge", "--verbose", "--ignore-default-opts", "--noreplace", "world"], bufsize=BUILD_LOG_BUFSIZE,
                            stdout=self.log_fd, stderr=self.log_fd, shell=False,
                            env=env, cwd=None).wait()
                if ret != 0:
                        raise XUtilsError("Target build failed, please see the log file %s" % self.log_file)

                ret = Popen(["xtc-update", "--automode", "-5"], bufsize=BUILD_LOG_BUFSIZE,
                            stdout=self.log_fd, stderr=self.log_fd, shell=False,
                            env=env, cwd=None).wait()
                if ret != 0:
                        raise XUtilsError("Target auto-update config files failed, please see the log file %s" % self.log_file)

        def release(self, build_info):
                """ Releasing rootfs.tgz """
                if build_info['success'] != True:
                        return

                archive = self.cfg['release']['archive_dir']
                compression = self.cfg['release']['compression']
                workdir = self.cfg['build']['workdir']

                rootfs_file = '%s-%s_root.tar.%s' % (build_info['pkg_name'], build_info['version'], compression)
                debugfs_file = '%s-%s_debuginfo.tar.%s' % (build_info['pkg_name'], build_info['version'], compression)
                dest_dir = "/".join([archive, build_info['category'],
                        build_info['pkg_name'], build_info['version'],
                        build_info['profile']])

                if not exists(dest_dir):
                        os.makedirs(dest_dir)

		if os.path.isfile(workdir + '/' + rootfs_file + '.gpg'):
			rootfs_file = rootfs_file + '.gpg'
			debugfs_file = debugfs_file + '.gpg'

                self.info('Releasing rootfs archive')
                self.log_fd.flush()
                ret = Popen(['mv', workdir + '/' + rootfs_file, dest_dir + '/' + rootfs_file],
                            bufsize=-1, stdout=self.log_fd, stderr=self.log_fd, shell=False, cwd=None).wait()
                if ret != 0:
                        raise XUtilsError("failed to move the rootfs archive")

		if os.path.isfile ( workdir + '/' + debugfs_file ):
	     	    self.info('Releasing debuginfo archive')
		    self.log_fd.flush()
		    ret = Popen(['mv', workdir + '/' + debugfs_file, dest_dir + '/' + debugfs_file],
		        bufsize=-1, stdout=self.log_fd, stderr=self.log_fd, shell=False, cwd=None).wait()
		    if ret != 0:
		        raise XUtilsError("failed to move the debuginfo archive")

def register(builder):
        builder.add_plugin(XBuilderBuildPlugin)

