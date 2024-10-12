#!/usr/bin/env bash

set -e
set -x

# Get the user and group names and IDs
echo "USER_NAME=$USER" > .devcontainer/.env
echo "USER_ID=$(id -u)" >> .devcontainer/.env

echo "GROUP_NAME=$GROUP" >> .devcontainer/.env
echo "GROUP_ID=$(id -g)" >> .devcontainer/.env

# Get the git local user name and email
# If not set, get the global user name and email
GIT_USERNAME=$(git config --local user.name)
if [ -z "$GIT_USERNAME" ]; then
  GIT_USERNAME=$(git config --global user.name)
fi
echo "GIT_USERNAME='$GIT_USERNAME'" >> .devcontainer/.env

GIT_EMAIL=$(git config --local user.email)
if [ -z "$GIT_EMAIL" ]; then
  GIT_EMAIL=$(git config --global user.email)
fi
echo "GIT_EMAIL='$GIT_EMAIL'" >> .devcontainer/.env