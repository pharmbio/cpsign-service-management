#!/bin/bash
# This script will extract the current version based on the github repository's tags

# Get current_version
CURRENT_VERSION=v$(git describe --tags --always | tr -d .)
regex='^v[0-9]{3}([ab][0-9]{1,}|rc[0-9]{1,})?$'

# Checking whether or not current version is tagged as release
if [[ "$CURRENT_VERSION" =~ $regex ]]; then
  echo "Current version tagged as release"
elif [ "$TRAVIS_BRANCH" == 'master' ]; then
  CURRENT_VERSION="${CURRENT_VERSION}-current"
else
  CURRENT_VERSION="${CURRENT_VERSION}-test"
fi
echo "Current version is: $CURRENT_VERSION"

export CURRENT_VERSION
