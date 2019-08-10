#!/bin/bash
sudo chown centos:centos /home/centos/deploy
sudo chown -R centos:centos /home/centos/deploy/*

sudo semanage permissive -a httpd_t
sudo setsebool -P httpd_can_network_connect true




sudo scl enable rh-python36 "virtualenv /home/centos/deploy/ccwebappenv"

sudo scl enable rh-python36 "source /home/centos/deploy/ccwebappenv/bin/activate && sudo pip install uwsgi flask"
sudo scl enable rh-python36 "pip install uwsgi flask"
sudo scl enable rh-python36 "pip install Flask_Ext"
sudo scl enable rh-python36 "pip install mysql-connector-python"
sudo scl enable rh-python36 "pip install -r /home/centos/deploy/requirements.txt" 
sudo chown centos:centos /home/centos/deploy/ccwebappenv/*
sudo chown centos:centos /home/centos/deploy/ccwebappenv/
