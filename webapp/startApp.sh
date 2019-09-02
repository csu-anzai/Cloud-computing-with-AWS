#!/bin/bash

sudo cp /home/centos/deploy/amazon-cloudwatch-agent.json /opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json
sudo cp -rf /home/centos/deploy/selinux /etc/sysconfig/selinux
sudo touch /opt/aws/amazon-cloudwatch-agent/logs/csye6225.log
sudo chmod 777 /opt/aws/amazon-cloudwatch-agent/logs/csye6225.log
sudo /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl -a fetch-config -m ec2 -c file:/opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json -s
sudo cp /home/centos/deploy/cloud.service /etc/systemd/system/cloud.service
sudo cp /home/centos/deploy/nginx.conf /etc/nginx/nginx.conf
sudo setenforce 0
sudo setenforce permissive
sudo systemctl daemon-reload
sudo systemctl start cloud
sudo systemctl restart cloud
sudo systemctl enable cloud
sudo usermod -a -G centos nginx
chmod 710 /home/centos
sudo nginx -t
sudo systemctl daemon-reload
sudo systemctl restart nginx
sudo systemctl enable nginx
