#!/bin/bash

mkdir -p ./nginx/certs

openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout ./nginx/certs/server.key \
  -out ./nginx/certs/server.crt \
  -subj "/C=US/ST=Local/L=Local/O=Local/OU=Dev/CN=localhost"