#!/bin/bash

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

docker build "$SCRIPT_DIR/rabbitmq-inited" -t rabbitmq-inited:latest
docker-compose -p scicatlive up -d