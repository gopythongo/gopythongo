.. This Source Code Form is subject to the terms of the Mozilla Public
   License, v. 2.0. If a copy of the MPL was not distributed with this
   file, You can obtain one at http://mozilla.org/MPL/2.0/.

GoPythonGo
==========

GoPythonGo delivers a build system that helps with realizing a build system that implements
`the GoPythonGo build process`

Premise
-------
GoPythonGo is built around 4 ideas:

 1. Python applications should always be run from a virtual environment.
 2. Builds should be as fast as possible, so Python Wheels should be used and should be cached.
 3. Applications should be deployed using manageable binary artifacts, like DEBs, RPMs or Docker containers and it
    should be easy to switch between their type.
 4. The binary artifacts should be as small as possible.

