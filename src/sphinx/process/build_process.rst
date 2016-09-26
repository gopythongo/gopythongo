.. _process:

.. This Source Code Form is subject to the terms of the Mozilla Public
   License, v. 2.0. If a copy of the MPL was not distributed with this
   file, You can obtain one at http://mozilla.org/MPL/2.0/.

The development, build and deployment chain
===========================================

In a nutshell, it's a Rube Goldberg machine
-------------------------------------------
Assuming you're using the `Git Flow <http://nvie.com/posts/a-successful-git-branching-model/>`_ development process,
typically what you want to happen when you push to a `feature/*` branch is this:

* Your repository host sends a webhook to your build server and code health analytics tools like landscape.io
* Your build server "builds" the affected code repository. For Python projects that usually means:
    - running the unit tests (perhaps against multiple Python versions using tox)
    - running static analysis tools (`flake8 <TODO>`_, `mypy <TODO>`_ et al)
    - analyzing and reporting code coverage

At a minimum, when you push to your `develop` branch or merge a pull request for a feature branch, you will want to
then execute further steps:

* packaging a `sdist` or `wheel` distribution and uploading it to a local Pypi package server
* Your build server then triggers the builds for downstream builds depending on the code that was just built. These
  builds will run their own tests using the new `sdist` or `wheel` distribution from the local Pypi package server.
* When the build chain reaches your actual applications, integration tests run using the updated code.
* Finally, an application build is triggered. The build server runs buildhelpers *build.py* inside a pbuilder
  chroot environment, downloading your application and its dependencies from your local Pypi server, installing
  them in a virtual environment inside the chroot and packaging that virtual environment as a package then
  moving that package into, for example, an apt package repository. Alternatively a Docker container might be
  provisioned with the application and uploaded to a Docker registry.
* An application build might trigger an automatic deployment build job which uses `Fabric <http://www.fabfile.org/>`_
  or similar toolkits like `mcollective` or `salt` to trigger application servers to download and install the updated
  packages or containers as well as execute a blue/green deployment strategy.


Vocabulary
==========

Throughout this document the individual parts of the above deployment chain are referred to by different names
usually encompassing different parts of the whole chain.


"Feature builds" vs "Develop builds" vs "Release candidate builds" vs "Hotfix builds" vs "Master builds"
--------------------------------------------------------------------------------------------------------
On your build server, you will have all four but depending on your build server they might be combined into a single
build job. The difference is how many steps you go through for eaco of these in your build process. For example, you
might not want to deploy feature builds. The above terminology is very much oriented towards `Git Flow` but the general
concept works for every branching/development model you might use.

Generally a *feature build* means building *feature branches*, often triggered by a feature branch becoming a pull
request. For JenkinsCI you can accomplish that with the
`GitHub Pull Request Builder <https://wiki.jenkins-ci.org/display/JENKINS/GitHub+pull+request+builder+plugin>`_ plugin.
`TravisCI supports it out of the box <http://blog.travis-ci.com/2012-08-13-build-workflow-around-pull-requests/>`_. and
`CircleCI does too <http://blog.circleci.com/github-status-support/>`_.

A *develop build* means building your cutting edge code, which in `Git Flow` terms means your ``develop`` branch. You
usually not only want to build commits to the develop branch, but also then build downstream code and deploy it to a
testing platform for further tests (integration tests and UI tests come to mind).

A *release build* means building project releases. In `Git FLow` terms you would do that while a ``release`` branch is
in its "hardening" phase. These builds are also usually deployed to testing servers.

A *master build* builds your ``master`` branch. This will always happen in `Git Flow` once a release branch is merged
into master and the release is promoted to production servers. The builds resulting from this are hosted on your live
servers and face your customers.

*Hotfix builds* are really similar to release builds. If you have separate teams building your next release while others
maintain your live servers and might release hotfixes, you might want to have a separate testing platform for hotfixes.
In any case, ``hotfix`` branches get merged into ``master`` when they are released to live servers.


"Libraries" vs "Applications" or alternatively "Apps" vs "Shells"
-----------------------------------------------------------------



"Library build job" vs "Application build job" vs "Deployment build job"
---------------------------------------------------------------------------
For the purpose of this process documentation this document distinguishes between these three build job types. A build
job is "a job configured on your build server". That definition does not always map one to one onto every availabe
build server. In some cases limitations of your build environment will require you to combine multiple build job types
into a single build job.

Library build job
'''''''''''''''''
A library build job builds a installable artifact, for Python that's basically always a `sdist` or `wheel` distributable
that gets uploaded to a Pypi server. That job should also follow basic code hygiene standards. I prefer the following:

* Run flake8 to enforce PEP-8 conformance
* Run additional static analysis tools like landscape.io
* Unit test code coverage should be ratcheted, so the build fails if coverage goes down from a previous build

If the library build is used by downstream applications, if you have a way for deploying feature branches of libraries,
but at the very least for your main development, release and master branches you will want to trigger downstream builds
of the libraries or applications using the library just built.

Application build job
'''''''''''''''''''''
Building an application in GoPythonGo terms is a *purely intellectual distinction from a library build*.

Deployment build job
''''''''''''''''''''


Build server limitations
------------------------
Obviously I can only speak to build environments that I have used before. So this is not a complete list of environments
that need special considerations or adaptations.

TravisCI
''''''''
As mentioned above, at the time of me writing this, TravisCI does not support downstream builds. There are various
ideas out there (for example
`this write-up by RightScale <http://eng.rightscale.com/2015/04/27/dependent-builds-in-travis.html>`_) on how to
deal with this. But this is definitely one area where you will have to adapt GoPythonGo to your specific environment.

