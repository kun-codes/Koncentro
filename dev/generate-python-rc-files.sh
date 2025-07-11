#!/bin/bash

# generate Python rc files from all .qrc files in src/resources
for qrc_file in $(find src/resources -maxdepth 1 -name "*.qrc"); do
    base_name=$(basename "$qrc_file" .qrc)
    pyside6-rcc "$qrc_file" -o "src/resources/${base_name}_rc.py"
done
