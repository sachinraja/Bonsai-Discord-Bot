#!/bin/bash

sudo apt install awscli -y

# define array of parameters
PARAMETERS=("MONGO_URI" "BONSAI_TOKEN")

paramString=""

# save parameters in string
write_param (){
    paramString+="$1=$(aws ssm get-parameter --name "$1" --with-decryption --region "us-west-1" --output text --query "Parameter.Value")\n"
}

for ((i=0; i < ${#PARAMETERS[@]}; i++));
do
write_param ${PARAMETERS[$i]}
done

# write parameters to file
echo -e $paramString | sudo cat > /home/ubuntu/Bonsai-Discord-Bot/.env
