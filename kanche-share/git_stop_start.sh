#!/bin/sh
#1. pull code:
sh stop.sh

echo "************1. pull code:************"
git pull origin master
#2. stop running old code:

echo "************2. stop running old code:************"
kill `ps ax | grep sharer | grep -v grep | awk '{print $1}'`

#3. start running new code:
echo "************3. start running new code:************"
LOCAL_PATH=`pwd`
sudo start-stop-daemon --start --quiet --background --chuid ubuntu --name sharer --pidfile sharer.pid --chdir $LOCAL_PATH --exec python-env/bin/python -- ./app/sharer.py

#4. tail log
echo "************4. tail log************"
tail -5 /var/log/kanche-share/sharer.log
