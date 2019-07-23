#!/usr/bin/env bash
#https://stackoverflow.com/questions/49553138/how-to-make-browser-trust-localhost-ssl-certificate
set -eu
org=localhost-ca
domain=localhost

cd `dirname $0`

sudo trust anchor --remove ca.crt || true

openssl genpkey -algorithm RSA -out ca.key
openssl req -x509 -key ca.key -out ca.crt \
    -subj "/CN=$org/O=$org"

openssl genpkey -algorithm RSA -out "$domain".key
openssl req -new -key "$domain".key -out "$domain".csr \
    -subj "/CN=$domain/O=$org"

openssl x509 -req -in "$domain".csr -days 365 -out "$domain".crt \
    -CA ca.crt -CAkey ca.key -CAcreateserial \
    -extfile <(cat <<END
basicConstraints = CA:FALSE
subjectKeyIdentifier = hash
authorityKeyIdentifier = keyid,issuer
subjectAltName = DNS:$domain
END
    )

sudo trust anchor ca.crt

echo "Note: this certificate is only trusted for localhost on this machine. Reopen your browser to update its certificates."
