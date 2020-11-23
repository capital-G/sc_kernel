#!/bin/bash

# https://stackoverflow.com/questions/3349105/how-to-set-current-working-directory-to-the-directory-of-the-script-in-bash
# set working dir to the dir of the script so relative paths work
cd "$(dirname "$0")"

pip install -e .[dev] --quiet

echo "Run flake8 test"
flake8
flake8_status=$?

echo "Run mypy test"
mypy .
mypy_status=$?

echo "Run unit tests"
coverage run --source '.' -m unittest discover
coverage_status=$?

coverage html

coverage report

coverage xml

if [[ -z "${OPEN_BROWSER_AFTER_TEST}" ]]; then
  echo "Set OPEN_BROWSER_AFTER_TEST to open webbrowser w/ coverage report after test"
else
  python -c "import os, webbrowser; webbrowser.open(f'file://{os.getcwd()}/coverage/index.html')"
fi

failedTests=0

if [ $flake8_status -ne 0 ]; then
  echo "Flake8 tests failed"
  failedTests=1
fi

if [ $mypy_status -ne 0 ]; then
  echo "MyPy tests failed"
  failedTests=1
fi

if [ $coverage_status -ne 0 ]; then
  echo "Unittests failed"
  failedTests=1
fi
