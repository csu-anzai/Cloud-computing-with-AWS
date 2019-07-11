#!/bin/bash
#shell script to create AWS network infrastructures
stack_name=STACK-NAME-summercloud2019-vpc
stack_create=$(aws cloudformation create-stack --template-body file://roles.yaml --stack-name STACK-NAME-summercloud2019-vpc --capabilities CAPABILITY_NAMED_IAM  )
echo "Stack is getting created...."
result=$(aws cloudformation wait stack-create-complete --stack-name STACK-NAME-summercloud2019-vpc)
if [[ -z "result" ]]; then
  echo "---Stack has not been created---"
else
  echo "---Stack has been successfully created---"
fi

