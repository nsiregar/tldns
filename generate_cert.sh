#!/bin/bash

# Generate self-signed certificate for testing
openssl req -x509 -newkey rsa:4096 -keyout server.key -out server.crt -days 365 -nodes \
    -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"

echo "Certificate and key generated: server.crt, server.key"