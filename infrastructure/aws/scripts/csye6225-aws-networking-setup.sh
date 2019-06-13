


read -p "eneter the CIDR" CIDR

read -p "enter the Availability zone1" AWSZone

read -p "enter the Availability zone2" AWSZone1

read -p "enter the Availability zone3" AWSZone2

read -p "enter the subnet cidr1" Subnetcidr

read -p "enter the subnet cidr2" Subnetcidr1

read -p "enter the subnet cidr3" Subnetcidr2

read -p "enter the Region"  VPCRegion


#cidr= echo -e  "enter the cidr block"

#echo "$CIDR"


echo "creating VPC"
vpcid=$(aws ec2 create-vpc  --cidr-block "$CIDR" --query 'Vpc.{VpcId:VpcId}' --output text| cut -f7)

echo "$vpcid"


vpctags=$(aws ec2 create-tags --resources "$vpcid" --tags "Key=Name,Value=Cloud2019VPC")
#echo "VPC tags  ${vpctags}" 


#vpc-exists --vpc-ids "$vpcid"



echo "creating subnets  -subnet1"
SUBNET_PUBLIC_ID=$(aws ec2 create-subnet --vpc-id "$vpcid" --cidr-block "$Subnetcidr" --availability-zone "$AWSZone" --query 'Subnet.{SubnetId:SubnetId}' --output text)



echo "creating subnet-2 in zone $AWSZone1"
SUBNET_PUBLIC_ID1=$(aws ec2 create-subnet --vpc-id "$vpcid" --cidr-block "$Subnetcidr1" --availability-zone "$AWSZone1" --query 'Subnet.{SubnetId:SubnetId}' --output text)


echo "creating subnet-3 in zone $AWSZone2"
SUBNET_PUBLIC_ID2=$(aws ec2 create-subnet --vpc-id "$vpcid" --cidr-block "$Subnetcidr2" --availability-zone "$AWSZone2" --query 'Subnet.{SubnetId:SubnetId}' --output text)



echo "creating gateway"

gwid=$(aws ec2 create-internet-gateway --query 'InternetGateway.{InternetGatewayId:InternetGatewayId}' --output text| cut -f7)
#echo "created gateways "$gwid"" 



echo "adding tag to Gateway"
aws ec2 create-tags --resources "$gwid" --tags "Key=Name,Value=Internet_gateway" --region "$VPCRegion"


echo "$gwid"
echo "attaching gateways to VPC"
aws ec2 attach-internet-gateway --vpc-id "$vpcid" --internet-gateway-id "$gwid"

echo "gateways attached"


echo "creating route table"

ROUTE_TABLE_ID_1=$(aws ec2 create-route-table --vpc-id "$vpcid" --query 'RouteTable.{RouteTableId:RouteTableId}' --output text| cut -f7)
echo "  Route Table ID '$ROUTE_TABLE_ID_1' CREATED."


echo "adding tags to Route table"

aws ec2 create-tags --resources "$ROUTE_TABLE_ID_1" --tags "Key=Name,Value=Routing_table" --region "$VPCRegion"

echo "creating route to internet "




RESULT=$(aws ec2 create-route --route-table-id "$ROUTE_TABLE_ID_1" --destination-cidr-block 0.0.0.0/0 --gateway-id "$gwid")

echo "  Route to '0.0.0.0/0' via Internet Gateway ID '$IGW_ID' ADDED to" \
  "Route Table ID '$ROUTE_TABLE_ID_1'."


echo "associating Subnet-1 with route table"
RESULT=$(aws ec2 associate-route-table --subnet-id "$SUBNET_PUBLIC_ID" --route-table-id "$ROUTE_TABLE_ID_1")
echo "  Public Subnet ID_1 '$SUBNET_PUBLIC_ID_1' ASSOCIATED with Public Route Table ID_1" "'$ROUTE_TABLE_ID_1'."



echo "associating subnet-2 with route table"
RESULT1=$(aws ec2 associate-route-table --subnet-id "$SUBNET_PUBLIC_ID1" --route-table-id "$ROUTE_TABLE_ID_1")




echo "associating subnet -3 with route table"

RESULT2=$(aws ec2 associate-route-table --subnet-id "$SUBNET_PUBLIC_ID2" --route-table-id "$ROUTE_TABLE_ID_1")



