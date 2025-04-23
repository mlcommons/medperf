LOGIN_EMAIL=$1
AUTH_STATUS=$(medperf auth status)

ALREADY_LOGGED_EMAIL=$(echo $AUTH_STATUS | grep -Eho "[[:graph:]]+@[[:graph:]]+")

if [ ! -z $ALREADY_LOGGED_EMAIL ]
then
    echo "Logging out of current logged in e-mail $ALREADY_LOGGED_EMAIL"
    medperf auth logout
fi

echo "Logging into email $LOGIN_EMAIL for this tutorial"
medperf auth login -e $LOGIN_EMAIL