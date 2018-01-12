#!/usr/bin/env bash

PYTHON_EXEC=python
PYTHON_ENV=python-env
PYTHON_ENV_EXEC=$PYTHON_ENV/bin/python
PYTHON_MODULES="procname suds requests lxml Pillow dt8601 cookies web.py simpleJson mongoengine img_rotate GitPython flask"
rm -rf $PYTHON_ENV
virtualenv --no-site-packages -p $PYTHON_EXEC $PYTHON_ENV
for m in $PYTHON_MODULES
do
	$PYTHON_ENV_EXEC -m pip install $m
done

$PYTHON_ENV_EXEC -m pip install pymongo==2.7
$PYTHON_ENV_EXEC -m easy_install suds
$PYTHON_ENV_EXEC -m easy_install PyExecJS

