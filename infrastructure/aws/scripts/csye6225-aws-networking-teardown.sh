#!/bin/bash
#
# Delete a VPC and its dependencies

if [ -z "$1" ]; then
    echo "usage: $0 <vpcid>"
    exit
fi
vpcid="$1"

echo "$vpcid"




vpcid=$(aws ec2 describe-vpcs --filter Name=tag-value,Values=”Cloud2019VPC” | grep -i VpcId | grep , |  sed -E 's/^.*(vpc-[a-z0-9]+).*$/\1/');
echo "$vpcid"
if [[ -z "$vpcid" ]]; then
  echo "--- VPC doesnt exisit ---"
  exit 0
else
  echo "---VPC exisit---"
fi


#route="$1-IPA5369-route"
#echo $route
# Delete subnets
for i in `aws ec2 describe-subnets --filters Name=vpc-id,Values="${vpcid}" | grep \"subnet- | sed -E 's/^.*(subnet-[a-z0-9]+).*$/\1/'`;
do

echo "Deleting subnet ID" $i
 aws ec2 delete-subnet --subnet-id=$i;
done


for i in `aws ec2 describe-internet-gateways --filters Name=attachment.vpc-id,Values="${vpcid}" | grep igw- | sed -E 's/^.*(igw-[a-z0-9]+).*$/\1/'`;
do
echo "Detaching internet Gateway" $i
 aws ec2 detach-internet-gateway --internet-gateway-id $i --vpc-id $vpcid;
echo "Deleting internet Gateway" $i
 aws ec2 delete-internet-gateway --internet-gateway-id $i;
done

for i in `aws ec2 describe-route-tables --filters Name=tag-value,Values=Routing_table| grep -i RouteTableId | grep , |  sed -E 's/^.*(rtb-[a-z0-9]+).*$/\1/'`;
do
echo "Deleting routing table" $i
aws ec2 delete-route-table --route-table-id=$i;
done


# Delete the VPC
aws ec2 delete-vpc --vpc-id ${vpcid}


