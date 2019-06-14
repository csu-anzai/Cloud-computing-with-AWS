#!/bin/bash
#shell script to create AWS network infrastructures
stack_name=STACK-NAME-summercloud2019-vpc
stack_create=$(aws cloudformation create-stack --template-body file://csye6225-cf-networking.yaml --stack-name STACK-NAME-summercloud2019-vpc --parameters  ParameterKey=Zone1,ParameterValue=us-east-1a ParameterKey=Zone2,ParameterValue=us-east-1c ParameterKey=Zone3,ParameterValue=us-east-1d)
echo "Stack is getting created...."
result=$(aws cloudformation wait stack-create-complete --stack-name STACK-NAME-summercloud2019-vpc)
if [[ -z "result" ]]; then
  echo "---Stack has not been created---"
else
  echo "---Stack has been successfully created---"
fi

