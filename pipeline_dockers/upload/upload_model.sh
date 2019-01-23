#!/bin/sh
if [ $1 = "-h" ]; then
 echo "Usage: $0 <modelingweb url> <keycloak url> <category> <model folder>"
 exit 0
fi
MW_URL=$1 
KEYCLOAK_URL=$2
CATEGORY=$3
FOLDER=$4
USERNAME=$(cat /mnt/api-info/user)
PASSWORD=$(cat /mnt/api-info/password)
#echo "$USERNAME:$PASSWORD"

RESULT=$(curl --data "grant_type=password&client_id=modelingweb&username=$USERNAME&password=$PASSWORD" ${KEYCLOAK_URL}/auth/realms/toxhq/protocol/openid-connect/token)
echo "Keycloak result: \n"$RESULT
TOKEN=$(echo $RESULT | jq -r '.access_token')

for mdl in $FOLDER/*jar; do
    echo "--------------------------------------------------------------------------------";
    echo "Trying to upload $mdl ..."
    echo "--------------------------------------------------------------------------------";
    RESULT=$(curl -F "category=$CATEGORY" -F "filecontent=@$mdl" --header "Authorization: bearer $TOKEN" "${MW_URL}/api/v1/models/fromFile";)
    echo "Result from command: "
    echo $RESULT
    sleep 0.5
done;	