#!/bin/bash

# install python dependencies
pip install -r api/requirements.txt

# set git config
git config --global user.email "abhishek@a6k.me"
git config --global user.name "Abhishek Kumar"
git config --global --add safe.directory /workspaces/notebooks
git config --global init.defaultBranch main