#!/bin/sh
kill `ps ax | grep maintainer | grep -v grep | awk '{print $1}'`
