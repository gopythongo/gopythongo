#!/bin/bash

# do nothing if fpm already exists
test -e /usr/local/bin/fpm && exit 0

EATMYDATA=""
if test -e /usr/bin/eatmydata; then
    EATMYDATA="/usr/bin/eatmydata"
fi

# make sure we have gem
if ! test -e /usr/bin/gem; then
    $EATMYDATA apt-get update
    $EATMYDATA apt-get --no-install-recommends -q -y \
        -o DPkg::Options::=--force-confold \
        -o DPkg::Options::=--force-confdef \
        install ruby ruby-dev libffi-dev libffi6 zlib1g-dev zlib1g ruby-ffi
fi

$EATMYDATA gem install fpm
