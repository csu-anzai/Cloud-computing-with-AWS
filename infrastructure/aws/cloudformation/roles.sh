#!/bin/bash
#shell script to create AWS network infrastructures
#echo"enter the stack name"
#read -p stackname

stack_create=$(aws cloudformation create-stack --template-body file://roles.yaml --stack-name roles --capabilities CAPABILITY_NAMED_IAM)
echo "Stack is getting created...."
result=$(aws cloudformation wait stack-create-complete --stack-name roles)
if [[ -z "result" ]]; then
  echo "---Stack has not been created---"
else
  echo "---Stack has been successfully created---"
fi

