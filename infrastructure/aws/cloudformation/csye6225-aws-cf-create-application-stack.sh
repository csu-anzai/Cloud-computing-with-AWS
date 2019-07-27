#!/bin/bash

#shell script to create AWS network infrastructures

#ami_name= '$1'
#ami_key='$2'


echo  "AMI : $1"

echo  "Key : $3"

echo "stackname: $4"

echo "VPC: $2"

echo "$stackname"

echo "subnet1 $5"
echo "subnet2 $6"












#vpcid=$(aws ec2 describe-vpcs --query 'Vpcs[?Tags[?Key=='Name']|[?Value=='cloudsu2019']].VpcId')

stack_create=$(aws cloudformation create-stack --template-body file://csye6225-cf-application.yaml --stack-name $4 --capabilities CAPABILITY_NAMED_IAM --parameters ParameterKey=AMI,ParameterValue=$1 ParameterKey=VPC,ParameterValue=$2 ParameterKey=AWSKEY,ParameterValue=$3 ParameterKey=Subnet1,ParameterValue=$5 ParameterKey=Subnet2,ParameterValue=$6)







echo "Stack is getting created...."

result=$(aws cloudformation wait stack-create-complete --stack-name $4)

if [[ -z "result" ]]; then

  echo "---Stack has not been created---"

else

  echo "---Stack has been successfully created---"

fi
