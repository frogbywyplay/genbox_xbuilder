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

XBUILDER_SYS_CFG = "/etc/xbuilder.conf"
XBUILDER_USER_CFG = ".xbuilder.conf"

XBUILDER_LOGFILE = 'build.log'
XBUILDER_REPORT_FILE = 'report.xml.bz2'

XBUILDER_DEFTYPE = "beta"
XBUILDER_TARGET_COMMIT = False

# Default values that can be modified in the config file
# Keep only N beta releases, put 0 to disable
XBUILDER_MAX_BETA_TARGETS = 5
XBUILDER_CLEAN_WORKDIR = True
XBUILDER_TARGET_COMMIT = True

XBUILDER_FEATURES = ''

XBUILDER_WORKDIR = "/usr/targets/xbuilder"
XBUILDER_ARCHIVE_DIR = "/opt/xbuilder"
XBUILDER_COMPRESSION = "xz"

XBUILDER_MAIL_FROM = "builder@wyplay.com"
XBUILDER_MAIL_TO = "integration@wyplay.com"
XBUILDER_MAIL_SMTP = "localhost"
XBUILDER_MAIL_LOG_SIZE = 20 * 1024
XBUILDER_MAIL_URI = "http://localhost/genbox-ng/xbuilder"

XBUILDER_NOTIFIER_URI = "http://localhost:9999/xbuilder"
XBUILDER_TYPES = [ "beta", "release" ]

XBUILDER_GPG_LOGFILE = 'gpg.log'
XBUILDER_GPG_LOGLEVEL = 20 # logging.INFO
