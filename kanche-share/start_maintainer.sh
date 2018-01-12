#!/bin/sh
LOCAL_PATH=`pwd`
sudo start-stop-daemon --start --quiet --background --chuid ubuntu --name maintainer --pidfile maintainer.pid --chdir $LOCAL_PATH --exec python-env/bin/python -- ./app/maintainer.py
