#!/bin/bash

__dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Check if the virtual environment directory exists
if [ ! -d "${__dir}/venv" ]; then
    echo "Virtual environment 'venv' not found. Creating..."
    python3 -m venv ${__dir}/venv
    source ${__dir}/venv/bin/activate
    pip install -r ${__dir}/requirements.txt
fi

source ${__dir}/venv/bin/activate
python ${__dir}/main.py $1 $2
deactivate
