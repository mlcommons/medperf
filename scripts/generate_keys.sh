openssl genpkey -algorithm ed25519 >$1
openssl pkey -in $1 -pubout -out $2
