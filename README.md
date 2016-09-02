GoPythonGo creates Python deployment artifacts
==============================================

You can go to many conferences and watch many talks on Youtube about Python deployment and they invariably
include a slide with a diagram that looks something like this:

    Developer -push-> GitHub/GitLab/BitBucket -webhook-> SomeBuildServer -magic-> Fabulous cloud stuff

GoPythonGo is a opinionated, extensible, well-structured and highly configurable implementation of the arrow
that says "magic".

This is still *under very active development*. Currently you can use it to build .deb packages to deploy virtual
environments using Apt. It will use pbuilder or Docker to do so, it can auto-increment your version strings or integrate
with other tools that do that, it can integrate with aptly to publish your packages to your server or Amazon S3. It
includes tools to integrate with Hashicorp Vault for secure package signing using GPG and implementing build server
SSL credential management. BUT, it's still changing all the time. That said, GoPythonGo is used to distribute
GoPythonGo, so there.

Basic philosophy
----------------
GoPythonGo is built to allow you to put things where they make the most sense. In practice, this means that the
command-line tool takes it's parameters from three sources: a configuration file, environment variables and
command-line parameters. This way, keep the configuration for *how to build* with your code in a checked-in config
file, but the configuration for *assembling* your build onm your build server server in environment variables or on
the command-line or a second configuration file that will be merged.


Getting started
---------------
On Debian:

  1. Install the GoPythonGo and Aptly distribution keys

        apt-key adv --keyserver hkp://keys.gnupg.net --recv-key DDB131CF1DF6A9CF8200799002CBD940A78049AF
        apt-key adv --keyserver keys.gnupg.net --recv-keys 9E3E53F19C7DE460

  2. Install GoPythonGo, [aptly](https://aptly.info), pbuilder and fpm. As `root`:

        echo "deb http://repo.gopythongo.com/nightly jessie main" > /etc/apt/sources.list.d/gopythongo.list
        echo "deb http://repo.aptly.info/ squeeze main" > /etc/apt/sources.list.d/aptly.list
        apt-get update
        apt-get --no-install-recommends install gopythongo aptly pbuilder ruby ruby-dev
        gem install fpm

  3. create a simple example project:

        mkdir -p /tmp/helloworld/helloworld
        cat > /tmp/helloworld/helloworld/__init__.py <<EOF
        # -* encoding: utf-8

        def main():
            print("hello world!")

        if __name__ == "__main__":
            main()
        EOF

        cat > /tmp/helloworld/setup.py <<EOF
        #!/usr/bin/env python -u
        import os
        from setuptools import setup

        setup(
            name='helloworld',
            version="1.0",
            packages=["helloworld",],
            entry_points={
                "console_scripts": [
                    "helloworld = helloworld:main"
                ],
            },
        )
        EOF

  4. Create a GoPythonGo configuration:

        cd /tmp/helloworld
        /opt/gopythongo/bin/gopythongo --init pbuilder_deb
        sed -e 's/mypackage/helloworld/g' .gopythongo/config > .gopythongo/config.1
        mv .gopythongo/config.1 .gopythongo/config
        sed -e 's/PACKAGENAME/helloworld/g' .gopythongo/fpm_opts > .gopythongo/fpm_opts.1
        mv .gopythongo/fpm_opts.1 .gopythongo/fpm_opts

  5. Create a Debian repository managed by aptly

        aptly repo create helloworld

  6. Build the helloworld package (-v enables verbose output):

        /opt/gopythongo/bin/gopythongo -v /opt/helloworld /tmp/helloworld

  7. You know what? Build it again and watch how the version number changes as GoPythonGo appends a revision number!
     Also, the second build will go much faster now that the initial setup is out of the way.

  8. Now install your creation

        dpkg -i helloworld_1.0~dev1-1.deb

  9. And run it:

        /opt/helloworld/bin/helloworld

 10. Go party!


Next steps
----------
If you create an aptly configuration file, you can use GoPythonGo to sign and push the package to, for example,
Amazon S3. Just look at GoPythonGo's own `.gopythongo` folder for examples.


Future features
---------------
In order of priority:

  1. Potentially add an additional class of plug-ins "composers" which execute even before the creation of the
     build environment to prepare the source tree for building. These might do things like: clean up temp files,
     request/download/install stuff or clone submodules.
  2. Add Docker Store support to build, tag and upload Docker containers
  3. Create integration and unittests
  4. Add RPM and createrepo support
