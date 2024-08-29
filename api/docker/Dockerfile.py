FROM python:3.12-bookworm

RUN pip install bandit semgrep

# RUN pip install setuptools wheel pyre-check fb-sapp
# RUN pyre init-pysa