#!/bin/bash

sudo gpasswd -a centos wheel

sudo cp /home/centos/deploy/webapp/cdScripts/cloud.service /etc/systemd/system/cloud.service
sudo cp /home/centos/deploy/webapp/cdScripts/nginx.conf /etc/nginx/nginx.conf

sudo cp -rf /home/centos/deploy/webapp/cdScripts/amazon-cloudwatch-agent.json /opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json
sudo mkdir /etc/systemd/system/nginx.service.d
printf "[Service]\nExecStartPost=/bin/sleep 0.1\n" | \
    sudo tee /etc/systemd/system/nginx.service.d/override.conf
sudo yum install jq -y
sudo touch /opt/aws/amazon-cloudwatch-agent/logs/csye6225.log
sudo chmod 777 /opt/aws/amazon-cloudwatch-agent/logs/csye6225.log

