#!/bin/bash
sudo systemctl stop cloud
sudo systemctl stop nginx
sudo chown centos:centos /home/centos/deploy/webapp/*
sudo rm -rf /home/centos/webapp
sudo rm -rf /opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.toml
sudo rm -rf /opt/aws/amazon-cloudwatch-agent/logs/csye6225.log
