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

import os

from os.path import isfile, exists, expanduser
from subprocess import Popen

from xtarget import XTargetBuilder, XTargetReleaseParser

from xintegtools.xbump import InvalidArgument, TargetEbuildUpdater
from xutils import XUtilsError, XUtilsConfig, info, vinfo, error

from xportage.xportage import XPortage

from consts import (
    XBUILDER_ARCHIVE_DIR,
    XBUILDER_CLEAN_WORKDIR,
    XBUILDER_COMPRESSION,
    XBUILDER_DEFTYPE,
    XBUILDER_FEATURES,
    XBUILDER_GPG_LOGFILE,
    XBUILDER_GPG_LOGLEVEL,
    XBUILDER_LOGFILE,
    XBUILDER_MAIL_FROM,
    XBUILDER_MAIL_LOG_SIZE,
    XBUILDER_MAIL_SMTP,
    XBUILDER_MAIL_TO,
    XBUILDER_MAIL_URI,
    XBUILDER_MAX_BETA_TARGETS,
    XBUILDER_NOTIFIER_URI,
    XBUILDER_SYS_CFG,
    XBUILDER_TARGET_COMMIT,
    XBUILDER_TYPES,
    XBUILDER_USER_CFG,
    XBUILDER_WORKDIR,
)


class XBuilder(object):
    def __init__(self, config=None, type=XBUILDER_DEFTYPE):
        self.log_fd = None
        self.build_info = {}
        self.plugin_list = []

        if config and not isfile(config):
            raise XUtilsError("Can't find config file %s" % config)

        self.type = type
        if type not in XBUILDER_TYPES:
            raise XUtilsError('Unkown build type %s' % type)

        self.config(config)

        workdir = self.cfg['build']['workdir']

        if self.cfg['build']['clean_workdir'] and exists(workdir):
            info('Cleaning workdir')
            Popen(['rm', '-rf', workdir], bufsize=-1, stdout=None, stderr=None, shell=False, cwd=None).wait()

        if not exists(workdir):
            os.makedirs(workdir)

        self.log_file = '%s/%s' % (workdir, XBUILDER_LOGFILE)
        self.log_fd = open(self.log_file, 'a')

        self.target_builder = XTargetBuilder(arch=r'*', stdout=self.log_fd, stderr=self.log_fd)
        self.xportage = XPortage(root='/')

        self.info('Loading plugins:', eol=False)
        for plugin in self.cfg['build']['plugins']:
            self.out('%s' % plugin, eol=False)
            p = __import__('xbuilder.plugins.%s' % plugin, fromlist=['register'])
            p.register(self)
        self.out('')

    def add_plugin(self, plugin):
        self.plugin_list.append(plugin(self.cfg, self.info, self.log_fd, self.log_file))

    def __del__(self):
        if (self.log_fd):
            self.log_fd.close()

    def config(self, config_files):
        if config_files is None:
            config_files = [XBUILDER_SYS_CFG, expanduser('~') + '/' + XBUILDER_USER_CFG]

        cfg = XUtilsConfig(config_files)
        self.cfg = {
            'target': {},
            'build': {},
            'jenkinsnotifier': {},
            'mail': {},
            'mirror': {},
            'notifier': {},
            'release': {},
            'gpg': {},
            'profilechecker': {}
        }
        self.cfg['target']['max_beta'] = int(cfg.get('target', 'max_beta', XBUILDER_MAX_BETA_TARGETS))
        self.cfg['target']['commit'] = cfg.get('target', 'commit', XBUILDER_TARGET_COMMIT)

        self.cfg['build']['clean_workdir'] = cfg.get('build', 'clean_workdir', XBUILDER_CLEAN_WORKDIR) == 'True'
        self.cfg['build']['workdir'] = cfg.get('build', 'workdir', XBUILDER_WORKDIR)
        self.cfg['build']['plugins'] = cfg.get('build', 'plugins', '').split()
        self.cfg['build']['features'] = cfg.get('build', 'features', XBUILDER_FEATURES)
        self.cfg['build']['enable_profilechecker'] = cfg.get('build', 'enable_profilechecker', True) == 'True'

        self.cfg['release']['archive_dir'] = cfg.get('release', 'archive_dir', XBUILDER_ARCHIVE_DIR)
        self.cfg['release']['compression'] = cfg.get('release', 'compression', XBUILDER_COMPRESSION)
        self.cfg['release']['tar_extra_opts'] = cfg.get('release', 'tar_extra_opts', str())
        self.cfg['release']['tag_overlays'] = cfg.get('release', 'tag_overlays', False)
        self.cfg['release']['tag_ebuilds'] = cfg.get('release', 'tag_ebuilds', False)

        self.cfg['jenkinsnotifier']['uri'] = cfg.get('jenkinsnotifier', 'uri', str())
        self.cfg['jenkinsnotifier']['username'] = cfg.get('jenkinsnotifier', 'username', str())
        self.cfg['jenkinsnotifier']['usertoken'] = cfg.get('jenkinsnotifier', 'usertoken', str())
        self.cfg['jenkinsnotifier']['jobname'] = cfg.get('jenkinsnotifier', 'jobname', str())
        self.cfg['mail']['smtp'] = cfg.get('mail', 'smtp', XBUILDER_MAIL_SMTP)
        self.cfg['mail']['from'] = cfg.get('mail', 'from', XBUILDER_MAIL_FROM)
        self.cfg['mail']['to'] = cfg.get('mail', 'to', XBUILDER_MAIL_TO)
        self.cfg['mail']['log_size'] = int(cfg.get('mail', 'log_size', XBUILDER_MAIL_LOG_SIZE))
        self.cfg['mail']['uri'] = cfg.get('mail', 'uri', XBUILDER_MAIL_URI)
        self.cfg['mirror']['user'] = cfg.get('mirror', 'user', '')
        self.cfg['mirror']['server'] = cfg.get('mirror', 'server', '')
        self.cfg['mirror']['pkey'] = cfg.get('mirror', 'pkey', '')
        self.cfg['mirror']['base_dir'] = cfg.get('mirror', 'base_dir', '')
        self.cfg['notifier']['uri'] = cfg.get('notifier', 'uri', XBUILDER_NOTIFIER_URI)
        self.cfg['gpg']['logfile'] = cfg.get(
            'gpg', 'logfile', os.path.join(self.cfg['build']['workdir'], XBUILDER_GPG_LOGFILE)
        )
        self.cfg['gpg']['loglevel'] = int(cfg.get('gpg', 'loglevel', XBUILDER_GPG_LOGLEVEL))

        self.cfg['profilechecker']['stop_on_warning'] = cfg.get('profilechecker', 'stop_on_warning', True) == 'True'
        self.cfg['profilechecker']['stop_on_error'] = cfg.get('profilechecker', 'stop_on_error', True) == 'True'
        del cfg

    def info(self, msg, eol=True):
        info(msg, eol)
        if eol:
            print >> self.log_fd, msg
        else:
            print >> self.log_fd, msg,

    def out(self, msg, eol=True):
        if eol:
            print msg
            print >> self.log_fd, msg
        else:
            print msg,
            print >> self.log_fd, msg,

    def vinfo(self, msg, eol=True):
        vinfo(msg, eol)
        if eol:
            print >> self.log_fd, msg
        else:
            print >> self.log_fd, msg,

    def __load_target_db(self, force=False):
        if not self.xportage.portdb or force:
            self.xportage.create_trees()

    def run(self, pkg_atom, version=None, arch=None, name=str()):
        ebuild = str()
        if not pkg_atom.startswith('='):
            ebuild = self.create_desc(pkg_atom, version, name)
        if not ebuild:
            ebuild = pkg_atom
        print ebuild
        self.prebuild(ebuild, arch)
        self.build(ebuild, arch)
        self.postbuild()
        self.release()
        return self.build_info['success']

    def create_desc(self, template, version=None, name=str()):
        """Create a new target description with xbump
                """
        try:
            updater = TargetEbuildUpdater(template)
        except InvalidArgument, e:
            raise XUtilsError(error=e.message)
        if not updater.is_target_ebuild():
            raise XUtilsError('%s does not conform with target ebuild definition.' % updater.template.abspath)
        updater.update_overlays(version[1])
        updater.update_revision(version[0])
        new_version = updater.compute_version(False, name[5:] if name else str())
        new_ebuild = updater.release_ebuild(new_version, True)
        self.__load_target_db(force=True)
        return new_ebuild

    def prebuild(self, target_ebuild, arch=None):
        self.info('Running prebuild step')
        for p in self.plugin_list:
            p.prebuild(target_ebuild, arch)

    def build(self, target_ebuild, arch=None):
        self.info('Running build step')
        self.__load_target_db()

        self.build_info['success'] = True

        for p in self.plugin_list:
            try:
                p.build(target_ebuild, self.target_builder, arch)
            except XUtilsError, e:
                error(str(e))
                self.build_info['success'] = False
                return

    def __extract_info(self):
        workdir = self.cfg['build']['workdir']

        release = XTargetReleaseParser().get(workdir, self.target_builder.cfg['release_file'])

        if not release:
            raise XUtilsError('Can\'t find release file')

        for k in ['name', 'version', 'arch']:
            if k not in release:
                raise XUtilsError('Missing key in release file (%s)' % k)

        cat, pn = release['name'].split('/')
        self.build_info['pkg_name'] = pn
        self.build_info['category'] = cat
        if 'version' not in self.build_info:
            self.build_info['version'] = release['version']
        self.build_info['arch'] = release['arch']

    def postbuild(self):
        self.info('Running postbuild step')
        if not 'pkg_name' in self.build_info:
            self.__extract_info()

        for p in self.plugin_list:
            p.postbuild(self.build_info)

    def release(self):
        self.info('Running release step')
        if not 'pkg_name' in self.build_info:
            self.__extract_info()

        for p in self.plugin_list:
            p.release(self.build_info)

    def cleanup(self):
        pass
