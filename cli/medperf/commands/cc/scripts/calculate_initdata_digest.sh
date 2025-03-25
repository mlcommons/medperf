dd if=/dev/zero of=zeroes bs=32 count=1
openssl dgst -sha384 --binary $1 | head -c 32 >init-data.digest
openssl dgst -sha256 --binary <(cat zeroes init-data.digest) | xxd -p -c32 >$2
