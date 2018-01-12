#!/bin/sh
LOCAL_PATH=`pwd`
sudo start-stop-daemon --start --quiet --background --chuid ubuntu --name sharer --pidfile sharer.pid --chdir $LOCAL_PATH --exec python-env/bin/python -- ./app/sharer.py
