#!/usr/bin/env bash

# Requirements:
# - Python 3.8+ with the mcgen package installed
# - The game version, as the first argument (default: snapshot)

echo "Purging temp directory..."
rm -r ./temp

echo "Purging generated directory..."
rm -r ./generated

echo "Purging processed directory..."
rm -r ./processed

version="${1:-snapshot}"
echo "Invoking mcgen with version: $version"
python -m mcgen --rawpath ./temp/raw --outpath ./processed --log INFO --version "$version"

echo "Copying generated data..."
cp -r ./temp/raw/generated ./generated
