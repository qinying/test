#!/bin/sh
kill `ps ax | grep restarter | grep -v grep | awk '{print $1}'`
