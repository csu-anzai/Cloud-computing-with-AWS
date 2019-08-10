#!/bin/bash

sudo gpasswd -a centos wheel

sudo cp /home/centos/deploy/cloud.service /etc/systemd/system/cloud.service
sudo cp /home/centos/deploy/nginx.conf /etc/nginx/nginx.conf

sudo cp -rf /home/centos/deploy/amazon-cloudwatch-agent.json /opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json
sudo cp -rf /home/centos/deploy/selinux /etc/sysconfig/selinux
sudo setenforce 0
sudo mkdir /etc/systemd/system/nginx.service.d
printf "[Service]\nExecStartPost=/bin/sleep 0.1\n" | \
    sudo tee /etc/systemd/system/nginx.service.d/override.conf
sudo yum install jq -y
sudo touch /opt/aws/amazon-cloudwatch-agent/logs/csye6225.log
sudo chmod 777 /opt/aws/amazon-cloudwatch-agent/logs/csye6225.log


sudo yum -y install centos-release-scl
sudo yum-config-manager --enable centos-sclo-rh-testing
sudo yum -y install rh-python36
sudo yum -y install epel-release
sudo yum -y install python-pip python-devel gcc nginx
sudo pip install virtualenv
