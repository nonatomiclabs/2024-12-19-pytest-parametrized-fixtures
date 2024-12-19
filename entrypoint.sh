#! /bin/bash
step=$1

if [ "$step" -gt 1 ]; then
    diff -d --minimal test_dummy_$((step - 1)).py test_dummy_$step.py -U 1000  | batcat --color=always
else
    batcat --color=always test_dummy_1.py
fi

set -x
pytest --setup-plan test_dummy_$step.py
