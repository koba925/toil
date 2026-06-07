#!/bin/bash

for toil_file in $(find . -name "toil.py" | sort); do
    if python "$toil_file" > /dev/null 2>&1; then
        echo "PASSED $toil_file"
    else
        echo "FAILED $toil_file"
    fi
done
