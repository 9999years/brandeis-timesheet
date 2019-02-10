#! /bin/sh
set -e
set -v

git pull --no-edit > /dev/null
python timesheet.py > timesheet.tex
latexmk -xelatex -halt-on-error -pvc- -pv- -quiet timesheet.tex
latexmk -norc -c
./make_email.py | sendmail -t