#!/bin/bash

# Run isort
isort --profile black .

# Run black
black .

# Run djlint
djlint . --reformat
