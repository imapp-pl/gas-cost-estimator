#!/bin/bash

# Check if an argument was provided
if [ $# -eq 0 ]; then
    echo "No argument provided. Please provide a directory path to your data."
    exit 1
fi

# if the argument is a directory, run the GUI
if [ -d "$1" ]; then
    docker run -it -p 5000:5000 -v "$1:/data" imapp-pl/gas-cost-estimator/gui:4.0 python3 /gui/web_api.py "$1"
else
    echo "The provided argument is not a directory: $1"
fi
