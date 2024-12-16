export STEPPATH=$(step path)
python /setup.py
step-ca --password-file=$STEPPATH/secrets/pwd.txt $STEPPATH/config/ca.json &

if [[ -n "$USE_PROXY" ]]; then
    STATUS="1"
    while [ "$STATUS" -ne "0" ]; do
        sleep 1
        step ca health --ca-url 127.0.0.1:8000
        STATUS="$?"
    done
    nginx -g "daemon off;"
fi
