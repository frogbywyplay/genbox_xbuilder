#!/usr/bin/python
#
# Copyright (C) 2006-2017 Wyplay, All Rights Reserved.
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
from functools import partial

from os import stat
from os.path import exists

from paramiko import AutoAddPolicy, SFTPClient, SSHClient
from paramiko.ssh_exception import AuthenticationException, BadHostKeyException, SSHException

from portage import config, create_trees
from portage_const import INCREMENTALS
from portage_versions import catsplit, pkgsplit

from subprocess import Popen

from urlparse import urlparse

from xutils import XUtilsError, info, warn

from xbuilder.plugin import XBuilderPlugin

SERVER='packages.wyplay.int'
USERNAME='integration'

class XBuilderBinpkgPlugin(XBuilderPlugin):

    def __init__(self, cfg, info, log_fd, log_file):
        super(XBuilderBinpkgPlugin, self).__init__(cfg, info, log_fd, log_file)
        self.cfg = {'root': '%s/root/' % cfg['build']['workdir'],
                    'basedir': str(),
                    'binpkgs': cfg['build']['binpkgs'],
                    'use_binpkg': True}

        # Test SSH connection
        ssh = SSHClient()
        try:
            ssh.set_missing_host_key_policy(AutoAddPolicy())
            ssh.connect(SERVER, username = USERNAME, look_for_keys = False)
        except BadHostKeyException:
            raise XUtilsError('Server host key verification failed.')
        except AuthenticationException:
            raise XUtilsError('Authentication to %s@%s failed.' % (USERNAME, SERVER))
        except SSHException:
            raise XUtilsError('Unable to establish a SSH connection to %s' % SERVER)
        except Exception,e:
            raise XUtilsError('Unable to establish a SSH connection to %s / reason: %s' % (SERVER, e.strerror))
        else:
            stdin, stdout, stderr = ssh.exec_command('touch foo && rm foo')
            if stderr.read():
                raise XUtilsError('User %s does not have sufficient permission on server %s to create/delete files.' % (USERNAME, SERVER))
        finally:
            try:
                ssh.close()
            except:
                pass

    def postbuild(self, build_info):

        def mymatch(x):
            return self.portage_db.xmatch('bestmatch-visible', x)

        def progress(filename, transferred, total):
            info(' * %s transfer in progress: %02d%%.\r' % (filename, transferred * 100 / total))

        # Get portage environment variables
        # Cannot do it earlier as in __init__, self.cfg['root'] does not exist
        my_config = config(config_root = self.cfg['root'], target_root = self.cfg['root'], config_incrementals = INCREMENTALS)
        self.cfg['basedir'] = urlparse(my_config['PORTAGE_BINHOST']).path
        if self.cfg['basedir'].startswith('/'):
            self.cfg['basedir'] = self.cfg['basedir'][1:]
        else:
            raise XUtilsError('Something is wrong with PORTAGE_BINHOST environment variable (value=%s)' % my_config['PORTAGE_BINHOST'])
        my_trees = create_trees(config_root = self.cfg['root'], target_root = self.cfg['root'])
        self.portage_db = my_trees[self.cfg['root']]['porttree'].dbapi

        if not my_config['PORTAGE_BINHOST']:
            warn('PORTAGE_BINHOST not set => binpkg disabled.')
            return

        # Convert binpkg list from [category/package] into [category/package-version.tbz2]
        # and silently ignore pkg not found in binpkgs
        tbz2_list = filter(lambda x: x is not None, map(mymatch, self.cfg['binpkgs']))

        # Initiate network connections
        # Use SFTP protocol to copy and work on server side
        ssh = SSHClient()
        try:
            ssh.set_missing_host_key_policy(AutoAddPolicy())
            ssh.connect(SERVER, username = USERNAME, look_for_keys = False)
        except SSHException:
            raise XUtilsError('Unable to establish a SSH connection to %s' % SERVER)

        try:
            sftp = SFTPClient.from_transport(ssh.get_transport())
            sftp.chdir(self.cfg['basedir'])
        except SSHException:
            raise XUtilsError('Unable to negotiate a SFTP session for %s' % SERVER)

        for tbz2 in tbz2_list:
            try:
                cp, version, release = pkgsplit(tbz2)
            except TypeError:
                warn('Incorrect atom for %s' % tbz2)
                continue
            cat, pv = catsplit(tbz2)

            # Check existence of [package-version.tbz2] in PKGDIR
            localpkg = '%s/All/%s.tbz2' % (my_config['PKGDIR'], pv)
            if exists(localpkg):
                info('Found %s.tbz2 locally under %s: skip its generation' % (pv, my_config['PKGDIR']))
                continue

            # Generate tbz2 for packages not found in PKGDIR (means missing on server)
            cmd = 'xexec quickpkg --include-config=y %s' % cp
            ret = Popen(cmd.split(), stdout=self.log_fd, stderr=self.log_fd, shell=False, cwd=None).wait()
            if ret != 0:
                warn("Unable to build binary package for %s" % tbz2)
                continue

            # Copy generated tbz2 on server
            localfile = '%s/All/%s.tbz2' % (my_config['PKGDIR'], pv)
            remotefile = '%s.tbz2' % pv
            if not exists(localfile):
                warn('%s not found => skip it.' % localfile)
                continue
            my_callback = partial(progress, remotefile)
            remote_attr = sftp.put(localfile, remotefile, callback = my_callback)
            if stat(localfile).st_size == remote_attr.st_size:
                info('%s successfully copied on server %s.' % (remotefile, SERVER))
            else:
                raise XUtilsError('Copy of %s on server %s is corrupted.' % (remotefile, SERVER))
            # Preserve Gentoo structure with symlinks
            try:
                available_cat = sftp.listdir('..')
                if cat not in available_cat:
                    sftp.mkdir('../%s' % cat, 0775)
                    sftp.chmod('../%s' % cat, 0775) # some servers may ignore mode from mkdir so force it with chmod.
                sftp.chdir('../%s' % cat)
                sftp.symlink('../All/%s' % remotefile, remotefile)
                sftp.chdir('../All')
            except IOError:
                warn('Something went wrong when creating symlink for %s' % remotefile)

        sftp.close()
        ssh.close()


def register(builder):
    builder.add_plugin(XBuilderBinpkgPlugin)
