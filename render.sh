#! /bin/sh
set -e
set -v

# don't worry about overwriting
git checkout settings.ini
git pull --no-edit > /dev/null
# apply local patch changes
patch settings.ini settings.patch

# update requirements
python3.7 -m pip install --user -r requirements.txt

# gen timesheet
python3.7 timesheet.py > timesheet.tex

# (re)render timesheet.pdf
rm -f timesheet.pdf
latexmk -xelatex -halt-on-error -pvc- -pv- timesheet.tex
latexmk -norc -c
