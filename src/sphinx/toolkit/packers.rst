.. _packers:

.. This Source Code Form is subject to the terms of the Mozilla Public
   License, v. 2.0. If a copy of the MPL was not distributed with this
   file, You can obtain one at http://mozilla.org/MPL/2.0/.

Packers: Packaging Virtualenvs
==============================

Currently GoPythonGo comes with two supported packaging subsystems:

  * `FPM <https://github.com/jordansissel/fpm/wiki>`: The swiss army-knife of packaging tools, supporting .deb, .rpm,
    .tar.gz, .zip... you name it. Using ``--packer=fpm`` you should be able to do basically whatever you need.

  * targz: Since not everybody wants to install a Ruby runtime and FPM, GoPythonGo can create simple .tar.gz output
    files itself when you use ``--packer=targz``.


Using the FPM packer
--------------------

