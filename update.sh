#!/usr/bin/env bash

# Requirements:
# - The server jar file, as the 1st argument
# - The game version, as the 2nd agument
# - Python 3.6+ with pyyaml package installed

if [ "$#" -ne 2 ]
then
    echo "Usage: ./update.sh <server_jar> <version>"
    exit 1
fi

echo "Using server jar: $1"
echo "Using version: $2"

echo "Updating version file..."
echo "$2" >| VERSION.txt

echo "Purging existing generated data..."
rm -rf ./generated

echo "Purging existing processed data..."
rm -rf ./processed

echo "Invoking data generator..."
java -cp "$1" net.minecraft.data.Main --server --reports

echo "Running data processor..."
python3 process.py --inpath=./generated --outpath=./processed
