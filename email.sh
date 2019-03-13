#!/usr/bin/env bash
set -e

# cron sets the path to like nothing so
PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
./render.sh
python3.7 make_email.py --send
