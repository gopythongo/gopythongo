.. _builders:

.. This Source Code Form is subject to the terms of the Mozilla Public
   License, v. 2.0. If a copy of the MPL was not distributed with this
   file, You can obtain one at http://mozilla.org/MPL/2.0/.

Builders: Supported build environments
======================================

Pbuilder Builder
----------------
Builds virtualenvs in a chroot using Debian's pbuilder. This has the drawback,
that GoPythonGo needs to run as root to utilize pbuilder correctly, as it needs
chroot privileges (you might be able to do something using fakeroot and setcap
cap_sys_chroot, but that's untested).


Docker Builder
--------------
Builds virtualenvs in a Docker container. This requires GoPythonGo to either
run as root or the user running GoPythonGo to be a member of the docker group.
To run Docker GoPythonGo relies on templated build Dockerfile which you can
customize to represent your later production runtime setup. Please note that
the build container used by the Docker Builder is not a container which you
should ship later, since it will likely contain compilers, header files and
other helpers. Instead create a minimal production Docker container from the
build container's output later, using the GoPythonGo Docker Store, for example.

The Docker build process runs in 3 steps:
    1. A build container is created using 'docker build' if it doesn't exist
       yet, containing sources, header files and compilers as needed.
    2. GoPythonGo executes inside that build container and builds a virtualenv
       using 'docker run'. This can't be done in step 1 because docker doesn't
       allow the mounting of host folders during build time.
    3. The build artifacts are extracted from the build container and the
       container is removed.

The build Dockerfile template must contain the following variables to build
the container:

    {{run_after_create}} - is a list of commands to run via the RUN directive
                           of the Dockerfile. Include it in your Dockerfile
                           template like this:
                               {% for cmd in run_after_create %}
                               RUN {{cmd}}
                               {% endfor %}

You can optionally use the following variables in the template:

    {{dependencies}} - resolves to a dictionary of distribution names to lists
                       of package names that are common dependencies required
                       to build virtualenvs for each platform. Distribution
                       names have the form 'debian/jessie'. This is just for
                       convenience.
                       For example: {{dependencies['debian/jessie']}} will
                       resolve to:
                           python,
                           python-pip,
                           python-dev,
                           python3-dev,
                           python-virtualenv,
                           virtualenv,
                           binutils,
                           libssl-dev,
                           libffi-dev

The build container is then run by GoPythonGo.


No isolation Builder
--------------------
As the name says, this Builder basically just runs all --after-create arguments
and then executes the 'inner' build, i.e. the part of GoPythonGo that would run
in a container with other Builders. This will definitely modify the build host's
filesystem. You should only really use this for build servers which already
isolate your builds (like TravisCI) and often don't give you the privileges to
run your own isolation layers anyway.
