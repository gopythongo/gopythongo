.. _process:

The development, build and deployment chain
===========================================

In a nutshell, it's a Rube Goldberg machine
-------------------------------------------
Assuming you're using the `Git Flow <http://nvie.com/posts/a-successful-git-branching-model/>`_ development process,
typically what you want to happen when you push to your `develop` branch or merge a pull request, is this:

  * Your repository host sends a webhook to your build server and code health analytics tools like landscape.io
  * Your build server "builds" the affected code repository. For Python projects that usually means:
      - running the unit tests (perhaps against multiple Python versions using tox) 
      - running static analysis tools (flake8 et al)
      - analyzing and reporting code coverage
      - packaging a `sdist` or `wheel` distribution and uploading it to a local Pypi package server
  * Your build server then triggers the builds for downstream builds depending on the code that was just built. These
    builds will run their own tests using the new `sdist` or `wheel` distribution from the local Pypi package server.
  * When the build chain reaches your actual applications, integration tests run using the updated code.
  * Finally, an application build is triggered. The build server runs buildhelpers *build.py* inside a pbuilder
    chroot environment, downloading your application and its dependencies from your local Pypi server, installing
    them in a virtual environment inside the chroot and packaging that virtual environment as a package then
    moving that package into, for example, an apt package repository. Alternatively a Docker container might be
    provisioned with the application and uploaded to a Docker registry.
  * An application build might trigger an automatic deployment build job which uses `Fabric <>`_ or similar toolkits
    like `mcollective` or `salt` to trigger application servers to download and install the updated packages or
    containers as well as execute a blue/green deployment strategy.
    

"Repository builds" vs "Application builds" vs "Deployment builds"
------------------------------------------------------------------


"Develop builds" vs "Release candidate builds" vs "Master builds"
-----------------------------------------------------------------
