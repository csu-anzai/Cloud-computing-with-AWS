stack_create=$(aws cloudformation create-stack --template-body file://csye6225-aws-cf-networking.yaml --stack-name summercloud2019-vpc --parameters ParameterKey=Zone1,ParameterValue=us-east-1a ParameterKey=Zone2,ParameterValue=us-east-1c ParameterKey=Zone3,ParameterValue=us-east-1d) 

result=$(aws cloudformation wait stack-create-complete --stack-name summercloud2019-vpc)

if [[ -z "result" ]]; then

  echo "---Stack has not been created---"

else

  echo "---Stack has been successfully created---"

fi



vpcid=$(aws ec2 describe-vpcs)
echo "$vpcid"

subnets=$(aws ec2 describe-subnets)
echo "$subnets"
read -p "enter the vpc" VPC
read -p "enter the subnet ids" Subnet1
read -p "enter the subnet id2" Subnet2
#!/bin/bash

echo "$VPC"
echo "This script is about to run another script."
./csye6225-aws-cf-create-application-stack.sh ami-09ec37d95f7d0f6fc "$VPC" cloudsu2019.pem.pub stack1 "$Subnet1" "$Subnet2"
echo "This script has just run another script."