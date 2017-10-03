GoPythonGo creates Python deployment artifacts
==============================================

You can go to many conferences and watch many talks on Youtube about Python deployment and they invariably
include a slide with a diagram that looks something like this:

    Developer -push-> GitHub/GitLab/BitBucket -webhook-> SomeBuildServer -magic-> Fabulous cloud stuff

GoPythonGo is a opinionated, extensible, well-structured and highly configurable implementation of the arrow
that says "magic".

GoPythonGo is built around 4 ideas:

  1. Python applications should always be run from a virtual environment.
  2. Builds should be as fast as possible, so Python Wheels should be used and should be cached.
  3. Applications should be deployed using manageable binary artifacts, like DEBs, RPMs or Docker containers and it
     should be easy to switch between their type.
  4. The binary artifacts should be as small as possible.

**This is still under very active development.** Currently you can use it to build .deb packages to deploy virtual
environments using Apt. It will use pbuilder or Docker to do so, it can auto-increment your version strings or integrate
with other tools that do that, it can integrate with aptly to publish your packages to your server or Amazon S3. It
includes tools to integrate with Hashicorp Vault for secure package signing using GPG and implementing build server
SSL credential management. BUT, it's still changing all the time. That said, GoPythonGo is used to distribute
GoPythonGo, so there.


Basic philosophy
----------------
GoPythonGo is built to allow you to put build configuration where it makes the most sense. In practice, this means 
that the command-line tool takes it's parameters from three sources: a configuration file, environment variables and
command-line parameters. This way, keep the configuration for *how to build* with your code in a checked-in config
file, but the configuration for *assembling* your build on your build server server in environment variables or on
the command-line or a second configuration file that will be merged.


Getting started
---------------
On Debian:

  1. Install the GoPythonGo and Aptly distribution keys

            apt-key adv --keyserver hkp://keys.gnupg.net --recv-key DDB131CF1DF6A9CF8200799002CBD940A78049AF
            apt-key adv --keyserver keys.gnupg.net --recv-keys 9E3E53F19C7DE460

  2. Install GoPythonGo, [aptly](https://aptly.info), pbuilder and fpm. As `root`:

            echo "deb http://repo.gopythongo.com/nightly/stretch gopythongo main" > /etc/apt/sources.list.d/gopythongo.list
            echo "deb http://repo.aptly.info/ squeeze main" > /etc/apt/sources.list.d/aptly.list
            apt-get update
            apt-get --no-install-recommends install gopythongo aptly pbuilder ruby ruby-dev
            gem install fpm

  3. create a simple example project:

            mkdir -p /tmp/helloworld/helloworld
            cat > /tmp/helloworld/helloworld/__init__.py <<EOF
            # -* encoding: utf-8 *-

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


Examples
--------
[Authserver](https://github.com/jdelic/authserver/) is a full project that I'm building using gopythongo. Just look in 
the .gopythongo folder and its README.

Next steps
----------
If you create an aptly configuration file, you can use GoPythonGo to sign and push the package to, for example,
Amazon S3. Just look at GoPythonGo's own `.gopythongo` folder for examples. You should also have a look at the output
of `--debug-config` to see how GoPythonGo loads configuration from the different sources (config file, environment
variables and command-line parameters).


Future features
---------------

  * Potentially add an additional class of plug-ins "composers" which execute even before the creation of the
    build environment to prepare the source tree for building. These might do things like: clean up temp files,
    request/download/install stuff or clone submodules.
  * Add Docker Store support to build, tag and upload Docker containers
  * Create integration and unittests
  * Add RPM and createrepo support


License
=======

GoPythonGo, meaning:

  1. It's source code as published on https://github.com/gopythongo/gopythongo
  2. It's documentation as published on https://github.com/gopythongo/gopythongo

is wholly subject to the Mozilla Public License v. 2.0 as published by the Mozilla Foundation and included with this
source code in the file "LICENSE". You can also find a copy of the full license at
https://www.mozilla.org/en-US/MPL/2.0/.

```
"Grant of license" PGP signature.

-----BEGIN PGP MESSAGE-----
Version: GnuPG v2

owGbwMvMwMHYcmwh8703tVcYT79MYgh/uf6QT2Zyal5xKi+XLQTwcvFyuecHVJZk
5Oe55+so5KYm5mXmpVuBxBUUDPUUPEvUixWK80uLklMVkvNTUhUSixUKSpNyMosz
UlMU8vMUMkpKCoqt9PXTM0sySpP0kvNz9dPzC8AGpucjMUHmGUHNS8lPLs1NzStJ
LMkEmkC+ibxcmcUK5Rn5OTmVCsWlSVmpySUKJfkKJRmpCr75VZk5OYkKASCTkxWg
/lYo0wM6wgDVyqRKFB1u+aV5KVCX5aUoZOYl55SmAJWVA50DVJhZzMuFHB6ZeWDd
aZk5qQpKPp7Orn7Brkp6CpH5pQrJiXlAcaAZiUClBZUK+WkQpaU5OQo5UAcllsD9
W15erpcLcYReflG6fmqebmiwvm+Ajz7Qyfp6IO8CI6soMa8EZFIOLCZ10QAvl2Mx
2J7ifKCTEkuBgVUEDJUGsNsVgD5L1VHwVEhML0pNBQUWzCGIVKAA9H9qEdiIktSi
3GKYu/EGKdB5ugrBqQUKRuY6CkYGhmYKugpe+XnAgPZNLC0qBQZaJ5MMCwMjBwMb
KxMwJR5h4OIUgCXPD578/z0W7Jo72f+aqvuyWVOSOr8wxYquDLkXHyTsaMi+x0r2
wW73X/5ap3l50u+VsYUyVF5+9/Xn7m8PzfzOPzO5u3lSgnVx75UbJWztsznWTP/g
+95NpYxBtf6FUppTT+ItC8f8NMH0n11f37A8Oli7OFqjStZ7Qv6rcwf1fGZfPl65
54T1loCm9LPCln2VhTeYL8kWhTYVCvw3U3aZK1FY0Vy54ATnP/Wq/OTEzQvuz7H9
cVTC6KT4Mvbnmq+29y358DpafJuGRPjBrG2KViIWkXMi9/5KdTlUdnBF0cP+yyt8
MuZcz6s7Xfm49kGEYa54dMm195/LhWZcZMldc+m7/gemNVsUDumtk9q8Z0vkpzX/
nyaEd5efOea0qMGEPSgkyazSZkVD87oN227OztyyPPloROaCd7kT2By/6n/WtVHf
wbLyA1vekSAfW9f/qeIOiSrG58tlHvBueLBv7k5vi+p7/9v7/Cvlz2REb72quLfh
4S3Hun21Ry1jynoqTI3z/xQeeRk3z3VBnK6Tor+bMr9ebMrGQ+s63Xb/VF/tVBeb
U1FpMU3m31/bvaslpt0tnr9tYTar+PKJd6e3XxHumdd1bcMUTx7r1//bHljHvciM
tNp4V5CtYf5db5WuwIgHUWlntEsjEperCUiEn+T6my5zn8ti09JtVYcnXli5MHz6
5poS68ifh5sW8Oqu4Vz+Tus5vynDtoTSlsm6AA==
=Z94o
-----END PGP MESSAGE-----
```
