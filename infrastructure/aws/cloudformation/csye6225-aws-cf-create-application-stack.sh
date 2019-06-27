#!/bin/bash

#shell script to create AWS network infrastructures

#ami_name= '$1'
#ami_key='$2'


echo  "AMI : $1"

echo  "AMI : $2"

echo "stackname: $3"

echo "$stackname"
stack_create=$(aws cloudformation create-stack --template-body file://csye6225-cf-application.yaml --stack-name $3 --parameters  ParameterKey=AMI,ParameterValue=$1 ParameterKey=Zone1,ParameterValue=us-east-1b ParameterKey=Zone2,ParameterValue=us-east-1c ParameterKey=AWSKEY,ParameterValue=$2)
echo "Stack is getting created...."

result=$(aws cloudformation wait stack-create-complete --stack-name $3)

if [[ -z "result" ]]; then

  echo "---Stack has not been created---"

else

  echo "---Stack has been successfully created---"

fi
