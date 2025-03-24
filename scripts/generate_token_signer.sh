openssl ecparam -name prime256v1 -genkey -noout -out $1
openssl req -new -x509 -key $1 -out $2 -days 365
