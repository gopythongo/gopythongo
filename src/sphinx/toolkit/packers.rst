.. _packers:

Packers: Packaging Virtualenvs
==============================

Currently GoPythonGo comes with two supported packaging subsystems:

  * `FPM <https://github.com/jordansissel/fpm/wiki>`: The swiss army-knife of packaging tools, supporting .deb, .rpm,
    .tar.gz, .zip... you name it. Using ``--packer=fpm`` you should be able to do basically whatever you need.

  * targz: Since not everybody wants to install a Ruby runtime and FPM, GoPythonGo can create simple .tar.gz output
    files itself when you use ``--packer=targz``.


Using the FPM packer
--------------------

