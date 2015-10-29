GoPythonGo
==========

GoPythonGo delivers a build script that helps with realizing a build system that implements
`the GoPythonGo build process`

The builder
-----------
The builder is designed to run inside a build environment in which it can
freely install operating system distribution packages and other build
artifacts. That means that it should run:

  * In a chroot, using a tool like pbuilder or
  * in a dedicated build VM or container (like it's the case on TravisCI or
    CircleCI.

