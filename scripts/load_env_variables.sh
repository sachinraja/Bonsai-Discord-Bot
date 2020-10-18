#!/bin/bash

# define array of parameters
PARAMETERS=("MONGO_URI" "BONSAI_TOKEN")

# write parameters to file
write_param (){
    echo $1=$(aws ssm get-parameter --name "$1" --with-decryption --output text --query "Parameter.Value") >> .env
}

for ((i=0; i < ${#PARAMETERS[@]}; i++));
do
write_param ${PARAMETERS[$i]}
done
