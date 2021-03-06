.. _docker:

.. This Source Code Form is subject to the terms of the Mozilla Public
   License, v. 2.0. If a copy of the MPL was not distributed with this
   file, You can obtain one at http://mozilla.org/MPL/2.0/.

Docker deployments
==================
Lightweight isolation (i.e. application containers) is currently clearly the future of service deployment. Docker
seems to be the defacto standard in this space.

The art of the minimal container
--------------------------------
As this is being written, an often-encountered problem with Docker containers on the official registry are
containers which have been built like VMs, containing everything and the kitchen-sink. You really don't want to ship
Linux kernel headers and the GCC compiler in every Docker container you deploy. Some so-called "best practices" might
imply doing that, but it's really a bad idea for a couple of reasons. Some of those are:

  * The bigger your container-based builds the bigger is the risk that your deployments aren't lightweight. This is
    a huge risk. There are still hundreds of pre-built containers out there which contain software that is vulnerable
    to Heartbleed. Don't be one of those developers.

  * The smaller your containers, the more shipable, convenient and plain usable they are.

  * ...

Build isolation containers and deployment containers
----------------------------------------------------
For Docker builds, GoPythonGo utilizes a build container to create an application package which is then being installed
into a production Docker container, pulling in minimal dependencies. The build isolation container is never stored.
This essentially replicates the pbilder or mock based build encironments in non-Docker GoPythonGo builds, but you end
up with a minimal Docker image to put in your registry and deploy across your servers.

