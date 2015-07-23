#!/bin/bash

NAME=docker-balancer
GUN_USER=nginx
WORKERS=2
DEPLOY_DIR=./

if [[ `grep ^nginx /etc/passwd` = "" ]]; then
  if [[ `grep ^www-data /etc/passwd` = "" ]]; then
     GUN_USER=$USER
  fi
fi

if [[ `grep ^nginx /etc/passwd` != "" ]]; then
   GUN_USER=nginx
fi

if [[ `grep ^www-data /etc/passwd` != "" ]]; then
   GUN_USER=wwww-data
fi


if [[ $1 = "" ]]; then
   LISTEN_ADDR=127.0.0.1
else
   LISTEN_ADDR=0.0.0.0
fi

cd $DEPLOY_DIR && cd ../

pwd

gunicorn $NAME:app -b $LISTEN_ADDR:8888 \
  --name $NAME \
  --workers $WORKERS \
  --user=$GUN_USER
