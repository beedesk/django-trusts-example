#!/bin/bash
set -e
virtualenv venv/
source ./venv/bin/activate
pip freeze | grep -v -f requirements.txt - | grep -v '^#' | xargs -r pip uninstall -y
pip install -r requirements.txt
source ./bin/localenv.sh
python apps/manage.py $@

