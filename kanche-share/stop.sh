#!/bin/sh
kill `ps ax | grep sharer | grep -v grep | awk '{print $1}'`
