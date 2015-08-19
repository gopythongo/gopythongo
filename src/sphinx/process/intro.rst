Introduction to the process
===========================

The problem with Python deployment
----------------------------------
There are many deployment models for Python. A lot of people resort to shipping source code and compiling
virtual environments on their servers, or installing Python programs in the interpreter shipped with the OS.
Some people also just push code to their servers using Git... whatever you are currently doing, it's worth
noting that *it might work for you*.

Obviously many people also use Docker to isolate their deployment artifacts into easily shippable containers.
Again, some people build the containers on the hardware where they'll later run.

We have seen time and time again that given a deployment platform, it's hard to design a deployment process
that will not at some point involve building code on the deployment platform. Some platforms like Heroku were
even built around the concept of "pushing code" to the deployment.

This collection of documents is about giving you a fully documented deployment process which offers the
following properties:

  * it's repeatable
  * it separates testing stages i.e. running unittests and running integration tests from building release artifacts
  * the components needed to run it can easily be swapped out
  * it produces shippable binary artifacts which can be deployed and upgraded independently and are versioned
    separately from your source code
  * it follows the same deployment process for release builds, release candidates and cutting-edge builds


The service model underlying GoPythonGo
---------------------------------------
When we designed our deployment model we made a couple of assumptions about the service types we were building
at our company:

  * There are services which can easily be put into containers and combined with other service containers on the
    same hardware or VM. These services typically use a fraction of the underlying available IO or CPU resources.
    This covers most microservices and applications you develop inside your company. For a Python application that
    means shipping a Docker container with a virtual environment or the application installed in the "main OS
    Python interpreter" inside the container.

  * There are services which typically can consume most if not all available IO and CPU resources on a server. That
    covers your typical database. Also, you might want to take advantage of 3rd party updates for these services or
    depdendency updates by your OS provider. Some of your user-facing applications might also fall under this group,
    where you'd rather deploy a single service instance to a VM or physical server. For a Python application that
    means shipping a virtual environment.


Deploying virtual environments
------------------------------
Over the last couple of years virtual environments have become the defacto isolation layer for Python. However one
of the central problems for copying them between servers, especially between build servers and application servers
is that they are not easily relocatable. You basically have to build them in the file system location where they
will be used later and obviously, if you copy them between servers, the underlying OS with its libraries and CPU
architecture has to be the same. `virtualenv` for a while tried to add support for relocating virtual environments
through the `--relocatable` command line flag, but that was a brittle affair that relied on searching and replacing
paths in shell scripts.

In fact GoPythonGo is precisely about providing you with reliable infrastructure to build virtual environments in
the file system location where you want to deploy them on your application server and making it easy to ship them
in manageable packages or Docker containers.


How does GoPythonGo address these requirements and assumptions
--------------------------------------------------------------
This document describes a process that fulfills the properties mentioned above. But it does so not independently of
previous art. Instead, it very much relies on established useful standards written by other smart people. In particular:

  * The `Git Flow <http://nvie.com/posts/a-successful-git-branching-model/>`_ development process
  * The `SemVer <http://semver.org/>`_ versioning system

GoPythonGo also uses a variety of supporting software to reach its goals:

  * GitHub, of course, but really any source code repository host which can send webhooks
  * The Jenkins build server (or TravisCI or CircleCI or whatever else you want to use)
  * pbuilder, a chroot-based build automation tool from the Debian project
  * My reimplementation of LaterPay's "buildhelpers" toolset
  * DjangoPyPi2, a pypi compatible server for serving Python packages
  * The docker registry project to keep pre-built Docker containers
  * Aptly, the excellent Debian repository management tool by @xxx
