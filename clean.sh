#!/bin/bash

# Run isort
isort .

# Run black
black .

# Run djlint
djlint . --reformat
