#!/bin/bash

set -e

BASEDIR="{{ basedir }}"
APPNAME="$(basedir $BASEDIR)"


case "$1" in
    configure)
        echo "****** Configuring $APPNAME in $BASEDIR"
        cd "$BASEDIR"

        if [ ! -e "/etc/mn-config/$APPNAME" ]; then
            echo "/etc/mn-config/$APPNAME not found. Will not link the app to"
            echo "daemontools without existing 12factor configuration."
            echo "You will have to link /etc/service/$APPNAME manually for it"
            echo "to be discovered by daemontools"
            exit 0;
        fi

        {% if service_folders %}
            if [ -e /etc/service ]; then
                echo "Creating service link(s)..."
                for folder in {{service_folders_str}}; do
                    ln -sv "/etc/service/$APPNAME_$folder" "$folder"
                done
            else
                echo "/etc/service not found. You will have to link"
                echo "/etc/service/$APPNAME manually for it to be discovered by"
                echo "daemontools."
            fi
        {% endif %}
    break
esac
