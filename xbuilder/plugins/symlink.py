import errno
import os
import shutil
import time

from xutils import warn

from xbuilder.plugin import XBuilderPlugin

BUILD_LOG_BUFSIZE = 1024 * 1024 * 2  # 2Mo should be enough


class XBuilderSymlinkPlugin(XBuilderPlugin):
    """ target are puts in arch_dir/category/name/arch/version with ACL set at 'arch' level
        legacy path were arch_dir/category/name/versin/arch with ACL set at 'name' level

        here we create compatibility symlinks in the legacy folders (to avoid breaking all tools)
    """

    def release(self, build_info):
        archive = self._archive_dir(
            build_info['category'], build_info['pkg_name'], build_info['version'], build_info['arch']
        )
        if not os.path.exists(archive):
            return
        legacy = os.path.join(
            self.cfg['release']['archive_dir'], build_info['category'], build_info['pkg_name'], build_info['version'],
            build_info['arch']
        )
        compat = os.path.dirname(legacy)
        self._makedirs(compat, exist_ok=True)
        retry = True
        while True:
            try:
                os.symlink(os.path.relpath(archive, compat), legacy)
                break
            except OSError as e:
                if retry and e.errno == errno.EEXIST:
                    if os.path.islink(legacy) and os.path.realpath(legacy) == os.path.realpath(archive):
                        break
                    bak = '%s.bak%s' % (legacy, int(time.time()))
                    warn('Unexpected folder found at %s: it will be renamed %s' % (legacy, bak), output=self.log_fd)
                    shutil.move(legacy, bak)
                    retry = False
                else:
                    raise


def register(builder):  # pragma: no cover
    builder.add_plugin(XBuilderSymlinkPlugin)
