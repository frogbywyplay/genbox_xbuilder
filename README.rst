--------
XBuilder
--------

Overview
========

Xbuilder is a genbox tool dedicated to create and make available a genbox target prebuilt.

Usage
=====

Basic usage
-----------

Xbuilder available options are::

    Usage: xbuilder [options] pkg_atom

    Builder tool for genbox-ng.

    Options:
      --ov-rev=OV_LIST      Fix an overlay revision (syntax:
                            "ov:rev[,ov:rev...]").
      -r PROFILE_REV, --rev=PROFILE_REV
                            Fix profile revision.
      -t BUILD_TYPE, --type=BUILD_TYPE
                            Set the type of build: beta (default) or release.
      -c CONFIG, --config=CONFIG
                            Use an alternate config file.
      -a ARCH, --arch=ARCH  Specify the target arch to build.
      --as=USER_VERSION     Use user ebuild's name
      -h, --help            show this help message and exit

Important points:

* Xbuilder default configuration file is ``/etc/xbuilder.conf``.
* Xbuilder requires a ``pkg_atom`` as a mandatory argument. ``pkg_atom`` is the target to build.
* ``-a ARCH`` argument is very important as it allows the builder to know exactly which target to build.

List available targets
----------------------

All available targets *( and so ``pkg_atom``)* can be listed as follow::

    [genboxbuilder] genbox ~ # xtarget -p
     * Available targets:
       * product-targets/frog

To build a specific target, an architecture and version are required. To list possibilities for a given target, simply run::

    [genboxbuilder] genbox ~ # xtarget -pv product-targets/frog
     * Available targets:
       * =product-targets/frog-0         ARCH="betty b2120_h410_stv910" USE="+redist prebuilt gpg debuginfo gpg redist"
       * =product-targets/frog-1.0.0.5   ARCH="betty" USE="+redist prebuilt gpg debuginfo gpg redist"
       * =product-targets/frog-1.2.0.21  ARCH="betty" USE="+redist prebuilt gpg debuginfo gpg redist"
       * =product-targets/frog-2.0.0.8   ARCH="betty" USE="+redist prebuilt gpg debuginfo gpg redist"
       * =product-targets/frog-2.0.0.19  ARCH="betty b2120_h410_stv910" USE="+redist prebuilt gpg debuginfo gpg redist"
       * =product-targets/frog-2.0.0.25  ARCH="betty b2120_h410_stv910" USE="+redist prebuilt gpg debuginfo gpg redist"
       * =product-targets/frog-2.0.0.27  ARCH="betty b2120_h410_stv910" USE="+redist prebuilt gpg debuginfo gpg redist"
       * =product-targets/frog-2.0.1.0   ARCH="betty b2120_h410_stv910" USE="+redist prebuilt gpg debuginfo gpg redist"
       * =product-targets/frog-2.0.1.1   ARCH="betty b2120_h410_stv910" USE="+redist prebuilt gpg debuginfo gpg redist"


Build a specific prebuilt
-------------------------

To specify a version, the syntax is: ``=pkg_atom-version`` *(as shown in the previous output)*. So to create a prebuilt for ``frog`` target version ``1.0.0.5`` and for a ``betty`` architecture:::

    [genboxbuilder] genbox ~ # xbuilder -a betty =product-targets/frog-1.0.0.5

.. note::
    If you do not specify a version in ``pkg_atom``, xbuilder will build the latest stable target.

Configuration file
------------------

Configuration file relies on INI format and has the following available options:


+--------------------+---------------------------+-----------------------------------------+-------------------------------------------------------------------------------+
| Section            | Option                    | Default value                           | Description                                                                   |
+====================+===========================+=========================================+===============================================================================+
| ``target``         | ``max_beta``              | ``5``                                   | Should do some clean in targets if there are more than ``max_beta`` *(Not     |
|                    |                           |                                         | implemented)*.                                                                |
|                    +---------------------------+-----------------------------------------+-------------------------------------------------------------------------------+
|                    | ``commit``                | ``False``                               | Not used.                                                                     |
+--------------------+---------------------------+-----------------------------------------+-------------------------------------------------------------------------------+
| ``build``          | ``clean_workdir``         | ``True``                                | Remove everything under ``workdir`` before building when set to ``True``.     |
|                    +---------------------------+-----------------------------------------+-------------------------------------------------------------------------------+
|                    | ``workdir``               | ``/usr/targets/xbuilder``               | Directory where to build target.                                              |
|                    +---------------------------+-----------------------------------------+-------------------------------------------------------------------------------+
|                    | ``plugins``               | *None*                                  | Space separated list of plugin to use to build target.                        |
|                    +---------------------------+-----------------------------------------+-------------------------------------------------------------------------------+
|                    | ``features``              | *None*                                  | Space separated list of features to enable/disable in portage. See FEATURES in|
|                    |                           |                                         | make.conf man page for more info.                                             |
|                    +---------------------------+-----------------------------------------+-------------------------------------------------------------------------------+
|                    | ``binpkgs``               | *None*                                  | Space separated list of package to binarize. It is disabled if PORTAGE_BINHOST|
|                    |                           |                                         | is not set.                                                                   |
+--------------------+---------------------------+-----------------------------------------+-------------------------------------------------------------------------------+
| ``release``        | ``archive_dir``           | ``/opt/xbuilder``                       | Place/directory to release target prebuilt tarball                            |
|                    +---------------------------+-----------------------------------------+-------------------------------------------------------------------------------+
|                    | ``tag_ebuilds``           | ``False``                               | Not used.                                                                     |
|                    +---------------------------+-----------------------------------------+-------------------------------------------------------------------------------+
|                    | ``tag_overlays``          | ``False``                               | Not used.                                                                     |
+--------------------+---------------------------+-----------------------------------------+-------------------------------------------------------------------------------+
| ``mail``           | ``smtp``                  | ``mail.wyplay.com``                     | SMTP server used to send mail.                                                |
|                    +---------------------------+-----------------------------------------+-------------------------------------------------------------------------------+
|                    | ``from``                  | ``builder@wyplay.com``                  | Mail sender.                                                                  |
|                    +---------------------------+-----------------------------------------+-------------------------------------------------------------------------------+
|                    | ``to``                    | ``integration@wyplay.com``              | Comma separated list of mail recipients.                                      |
|                    +---------------------------+-----------------------------------------+-------------------------------------------------------------------------------+
|                    | ``log_size``              | ``20 * 1024``                           | Log file sent with mail will be limited to ``log_size`` bytes.                |
|                    +---------------------------+-----------------------------------------+-------------------------------------------------------------------------------+
|                    | ``uri``                   | ``http://localhost/genbox-ng/xbuilder`` | Server to lookup to find more info about built target.                        |
+--------------------+---------------------------+-----------------------------------------+-------------------------------------------------------------------------------+
| ``notifier``       | ``uri``                   | ``http://localhost:9999/xbuilder``      | URL where to do the HTTP POST request.                                        |
+--------------------+---------------------------+-----------------------------------------+-------------------------------------------------------------------------------+
| ``gpg``            | ``logfile``               | ``gpg.log``                             | When GPG plugin is used, logs are redirected to this file during GPG          |
|                    |                           |                                         | encryption.                                                                   |
|                    +---------------------------+-----------------------------------------+-------------------------------------------------------------------------------+
|                    | ``loglevel``              | ``20``                                  | GnuPG logger verbosity level.                                                 |
+--------------------+---------------------------+-----------------------------------------+-------------------------------------------------------------------------------+
| ``profilechecker`` | ``stop_on_warning``       | ``False``                               | Will raise an exception when set to True if profile-checker detects minor     |
|                    |                           |                                         | problems in the profile.                                                      |
|                    +---------------------------+-----------------------------------------+-------------------------------------------------------------------------------+
|                    | ``stop_on_error``         | ``True``                                | Will raise an exception and so stop the build when set to True if             |
|                    |                           |                                         | profile-checker detects major problems in the profile.                        |
+--------------------+---------------------------+-----------------------------------------+-------------------------------------------------------------------------------+

Jenkins notifier plugin
=======================

This section is about Jenkins notifier plugin and things to know about it to correctly run it.

Jenkins notifier features and limitations
-----------------------------------------

The jenkins notifier plugin handles the following features:

* Skip notification on build failure.
* Authentication to the server using user api token.
* CSRF protection token as an HTTP request header if available.
* jobname can be based on input parameters like package, arch or category.
* It sets a 60 seconds delay before building the job to ensure that ``build`` plugin release phase is done.

Currently, jenkins notifier plugin has the following limitations:

* It is not able to trigger a build with parameters.
* It cannot trigger more than one job on a given server.

Jenkins job configuration
-------------------------

* Job can be triggered remotely by checking the appropriate box in job configuration menu.
* Job authentication token is a SHA1 hash of its name.
