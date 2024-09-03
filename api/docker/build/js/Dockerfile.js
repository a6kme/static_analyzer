# Currently not able to figure out how to generate an eslint configuration file for JavaScript
# hence will just use semgrep with javascript specific rule sets

# Starting with python base image rather than node base image, since semgrep is a python package
# and thats what we will be using
FROM python:3.12-bookworm

RUN pip install semgrep
