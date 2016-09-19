#!/bin/bash

echo "Start provneo4j-api docker container"


cd /var/lib/neo4j && . /docker-entrypoint.sh neo4j

echo "hello"

