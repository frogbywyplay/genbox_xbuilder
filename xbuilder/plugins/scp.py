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
from __future__ import with_statement

from os import stat, listdir
from os.path import exists, realpath
from functools import partial
import sys

try:
    # filter warning from pycrypto (imported by paramiko)
    # "PowmInsecureWarning: Not using mpz_powm_sec."
    import warnings as _warnings
    from Crypto.pct_warnings import PowmInsecureWarning
    _warnings.simplefilter('ignore', category=PowmInsecureWarning, append=1)
except ImportError:
    pass

from paramiko import AutoAddPolicy, SFTPClient, SSHClient
from paramiko.config import SSHConfig
from paramiko.ssh_exception import AuthenticationException, BadHostKeyException, SSHException

from xutils import output, XUtilsError

from xbuilder.plugin import XBuilderPlugin


class XBuilderScpPlugin(XBuilderPlugin):
    def __init__(self, cfg, info, log_fd, log_file):
        super(XBuilderScpPlugin, self).__init__(cfg, info, log_fd, log_file)
        self.ssh = self.cfg['scp'].copy()

        config = SSHConfig()
        with open('/etc/ssh/ssh_config', 'r') as f:
            config.parse(f)
        if 'user' in config.lookup(self.ssh['server']):
            self.ssh['user'] = config.lookup(self.ssh['server'])['user']
        else:
            output.error('No config for "Host %s" in /etc/ssh/ssh_config' % self.ssh['server'])
            raise XUtilsError('SSH config is incomplete.')

        # Test SSH connection
        ssh = SSHClient()
        try:
            ssh.set_missing_host_key_policy(AutoAddPolicy())
            ssh.connect(self.ssh['server'], username = self.ssh['user'], allow_agent = True, compress = True)
        except BadHostKeyException, e:
            output.error('BadHostKeyException: %s' % str(e))
            raise XUtilsError('Server host key verification failed.')
        except AuthenticationException, e:
            output.error('AuthenticationException: %s' % str(e))
            raise XUtilsError('Authentication to %s failed.' % self.ssh['server'])
        except SSHException, e:
            output.error('SSHException: %s' % str(e))
            raise XUtilsError('Unable to establish a SSH connection to %s' % self.ssh['server'])
        finally:
            stdin, stdout, stderr = ssh.exec_command(  # pylint: disable=unused-variable
                'touch %s/foo && rm %s/foo' % (self.ssh['base_dir'], self.ssh['base_dir'])
            )
            if stderr.read():
                raise XUtilsError(
                    'User does not have sufficient permission on server %s to create/delete files.' %
                     self.ssh['server']
                )
            ssh.close()

    def release(self, build_info):
        def progress(filename, transferred, total):
            sys.stdout.write(' * %s transfer in progress: %02d%%.\r' % (filename, transferred * 100 / total))
            sys.stdout.flush()

        if not build_info['success']:
            self.info('Build failure: nothing to copy on %s' % self.ssh['server'])
            return

        ssh = SSHClient()
        try:
            ssh.set_missing_host_key_policy(AutoAddPolicy())
            ssh.connect(self.ssh['server'], username = self.ssh['user'], allow_agent = True, compress = True)
        except SSHException, e:
            output.error('SSHException: %s' % str(e))
            raise XUtilsError('Unable to establish a SSH connection to %s' % self.ssh['server'])

        dest_dir = '/'.join([
            self.ssh['base_dir'], build_info['category'], build_info['pkg_name'], build_info['version'],
            build_info['arch']
        ])
        stdin, stdout, stderr = ssh.exec_command('mkdir -p %s' % dest_dir)  # pylint: disable=unused-variable
        if stderr.read():
            raise XUtilsError('Unable to create directory %s on server %s' % (dest_dir, self.ssh['server']))

        src_dir = str()
        files = [
            '%s-%s_root.tar.xz' % (build_info['pkg_name'], build_info['version']),
            '%s-%s_debuginfo.tar.xz' % (build_info['pkg_name'], build_info['version']),
            '%s-%s_overlaycaches.tar.xz' % (build_info['pkg_name'], build_info['version']),
        ]

        for f in listdir(self.cfg['build']['workdir']):
            if f.endswith('_root.tar.xz'):
                src_dir = self.cfg['build']['workdir']
                break
            elif f.endswith('_root.tar.xz.gpg'):
                src_dir = self.cfg['build']['workdir']
                files = map(lambda x: '%s.gpg' % x, files)
                break
        if not src_dir:
            src_dir = self.cfg['release']['archive_dir']

        try:
            sftp = SFTPClient.from_transport(ssh.get_transport())
            sftp.chdir(dest_dir)
        except SSHException:
            raise XUtilsError('Unable to negotiate a SFTP session for %s' % self.ssh['server'])

        for f in files:
            filepath = realpath(src_dir + '/' + f)
            if not exists(filepath):
                self.info('%s not found => skip it.' % f)
                continue
            my_callback = partial(progress, f)
            remote_attr = sftp.put(filepath, f, callback=my_callback)
            if stat(filepath).st_size == remote_attr.st_size:
                self.info('%s successfully copied on server %s.' % (f, self.ssh['server']))
            else:
                raise XUtilsError('Copy of %s on server %s is corrupted.' % (f, self.ssh['server']))

        sftp.close()
        ssh.close()


def register(builder):  # pragma: no cover
    builder.add_plugin(XBuilderScpPlugin)
