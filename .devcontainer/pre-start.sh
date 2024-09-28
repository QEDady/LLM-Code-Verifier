#!/usr/bin/env bash

echo "USER_NAME=$USER" > .env
echo "USER_ID=$(id -u)" >> .env

echo "GROUP_NAME=$GROUP" >> .env
echo "GROUP_ID=$(id -g)" >> .env
