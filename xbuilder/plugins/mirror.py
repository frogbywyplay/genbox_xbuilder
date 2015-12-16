#!/usr/bin/python
#
# Copyright (C) 2006-2016 Wyplay, All Rights Reserved.
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
from __future__ import print_function

from os import stat
from os.path import exists, realpath
from functools import partial
from paramiko import AutoAddPolicy, SFTPClient, SSHClient
from paramiko.ssh_exception import AuthenticationException, BadHostKeyException, SSHException
from portage.output import colorize
from xbuilder.plugin import XBuilderPlugin
from xutils import XUtilsError

class XBuilderMirrorPlugin(XBuilderPlugin):
    def __init__(self, cfg, info, log_fd, log_file):
        super(XBuilderMirrorPlugin, self).__init__(cfg, info, log_fd, log_file)
        self.ssh = self.cfg['mirror'].copy()
        for k,v in self.ssh.items():
            if not v and k != 'pkey':
                raise XUtilsError('[mirror plugin]: mandatory parameter \'%s\' not set.' % k)
        # Test SSH connection
        ssh = SSHClient()
        try:
            ssh.set_missing_host_key_policy(AutoAddPolicy())
            ssh.connect(self.ssh['server'], username = self.ssh['user'], key_filename = self.ssh['pkey'])
        except BadHostKeyException:
            raise XUtilsError('Server host key verification failed.')
        except AuthenticationException:
            raise XUtilsError('Authentication to %s@%s failed.' % (self.ssh['user'], self.ssh['server']))
        except SSHException:
            raise XUtilsError('Unable to establish a SSH connection to %s' % self.ssh['server'])
        finally:
            stdin, stdout, stderr = ssh.exec_command('touch %s/foo && rm %s/foo' % (self.ssh['base_dir'], self.ssh['base_dir']))
            if stderr.read():
                raise XUtilsError('User %s does not have sufficient permission on server %s to create/delete files.' % (self.ssh['user'], self.ssh['server']))
            ssh.close()

    def release(self, build_info):

        def progress(filename, transferred, total):
            print(colorize('fuchsia', ' * %s transfer in progress: %02d%%.\r' % (filename, transferred * 100 / total)), end = '\r')

        if build_info['success'] != True:
            return

        ssh = SSHClient()
        try:
            ssh.set_missing_host_key_policy(AutoAddPolicy())
            ssh.connect(self.ssh['server'], username = self.ssh['user'], key_filename = self.ssh['pkey'])
        except SSHException:
            raise XUtilsError('Unable to establish a SSH connection to %s' % self.ssh['server'])

        dest_dir = '/'.join([self.ssh['base_dir'], build_info['category'], build_info['pkg_name'], build_info['version'], build_info['arch']])
        stdin, stdout, stderr = ssh.exec_command('mkdir -p %s' % dest_dir)
        if stderr.read():
            raise XUtilsError('Unable to create directory %s on server %s' % (dest_dir, self.ssh['server']))

        src_dir = str()
        for f in listdir(self.cfg['build']['workdir']):
            if f.endswith('_root.tar.gz'):
                src_dir = self.cfg['build']['workdir']
        if not src_dir:
            src_dir = self.cfg['release']['archive_dir']
        files = list()
        files += ['%s-%s_root.tar.gz' % (build_info['pkg_name'], build_info['version'])]
        files += ['%s-%s_debuginfo.tar.gz' % (build_info['pkg_name'], build_info['version'])]
        files += [rootfs_file + '.gpg']
        try:
            sftp = SFTPClient.from_transport(ssh.get_transport())
            sftp.chdir(dest_dir)
        except SSHException:
            raise XUtilsError('Unable to negotiate a SFTP session for %s' % self.ssh['server'])

        for f in files:
            filepath = realpath(src_dir + '/' + f)
            if not exists(filepath):
                self.info(colorize('yellow', '%s not found => skip it.' % f))
                continue
            my_callback = partial(progress, f)
            remote_attr = sftp.put(filepath, f, callback = my_callback)
            if stat(filepath).st_size == remote_attr.st_size:
                self.info('%s successfully copied on server %s.' % (f, self.ssh['server']))
            else:
                raise XUtilsError('Copy of %s on server %s is corrupted.' % (f, self.ssh['server']))

        sftp.close()
        ssh.close()

def register(builder):
    builder.add_plugin(XBuilderMirrorPlugin)
