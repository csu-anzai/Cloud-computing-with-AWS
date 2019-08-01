sudo pip3.6 install mysql-connector
sudo cp -rf /home/centos/deploy/webapp/amazon-cloudwatch-agent.json /opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json
sudo yum install jq -y
sudo touch /opt/aws/amazon-cloudwatch-agent/logs/csye6225.log
sudo chmod 777 /opt/aws/amazon-cloudwatch-agent/logs/csye6225.log
sudo /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl -a fetch-config -m ec2 -c file:/opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json -s
cd /home/centos/deploy/webapp/
sudo python3.6 Cloud_WebApp.py
