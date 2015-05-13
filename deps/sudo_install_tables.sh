#!/bin/bash
python_tables_installed=`pip list | grep '^tables (' | wc -l`
if [ "$python_tables_installed" > "0" ]; then
    exit 0
fi
echo "Installing python tables"
sudo apt-get install libblas3gf
sudo apt-get install liblapack3gf
sudo apt-get install libhdf5-serial-dev
pip install tables
