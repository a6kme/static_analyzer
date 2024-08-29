#!/bin/bash

# Build the Docker images
docker build -f Dockerfile.py -t a6kme/static-analyzer-py .
docker build -f Dockerfile.js -t a6kme/static-analyzer-js .