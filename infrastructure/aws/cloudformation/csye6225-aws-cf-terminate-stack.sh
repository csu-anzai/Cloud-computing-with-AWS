#!/bin/bash
#shell script to delete AWS network infrastructure
stack_name= STACK-NAME-summercloud2019-vpc
stack_delete=$(aws cloudformation delete-stack --stack-name  STACK-NAME-summercloud2019-vpc)
echo "Stack is getting deleted...."
result=$(aws cloudformation wait stack-delete-complete --stack-name  STACK-NAME-summercloud2019-vpc)
if [[ -z "result" ]]; then
  echo "---Stack has not been deleted---"
else
  echo "---Stack has been successfully deleted---"
fi

