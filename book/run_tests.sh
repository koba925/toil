#!/bin/bash

for test_file in $(find . -name "test_*.py" | sort); do
    if python -m pytest "$test_file" > /dev/null 2>&1; then
        echo "PASSED $test_file"
    else
        echo "FAILED $test_file"
    fi
done
