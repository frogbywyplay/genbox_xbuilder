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

import requests
from requests.exceptions import RequestException

from xutils import output

from xbuilder.plugin import XBuilderPlugin


class XBuilderNotifierPlugin(XBuilderPlugin):
    def __notify(self, step, params):
        output.info('Notifier: send %s information' % step)
        params['step'] = step
        try:
            requests.get(self.cfg['notifier']['uri'], params)
            return None
        except RequestException as e:
            return output.error('HTTPError: %s' % e)

    def prebuild(self, target_ebuild, arch=None):
        # 2013-10-09: no need
        pass

    def build(self, target_ebuild, target_builder, arch=None):
        # 2013-10-09: no need
        pass

    def postbuild(self, build_info):
        # 2013-10-09: no need
        # params = build_info.copy()
        # self.__notify('postbuild', params)
        pass

    def release(self, build_info):
        params = build_info.copy()
        self.__notify('release', params)


def register(builder):  # pragma: no cover
    builder.add_plugin(XBuilderNotifierPlugin)
