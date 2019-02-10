#! /bin/sh
set -e
set -v

git pull --no-edit > /dev/null
python3.7 -m pip install --user -r requirements.txt
python3.7 timesheet.py > timesheet.tex
latexmk -xelatex -halt-on-error -pvc- -pv- -quiet timesheet.tex
latexmk -norc -c
