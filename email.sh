#!/usr/bin/env bash
set -e
set -v

# cron sets the path to like nothing so
PATH="/home/pi/.local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
./render.sh
./make_email.py | sendmail -t
