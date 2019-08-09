
sudo chown centos:centos /home/centos/deploy/webapp
sudo chown -R centos:centos /home/centos/deploy/webapp/*

sudo semanage permissive -a httpd_t
virtualenv /home/centos/deploy/webapp/ccwebappenv

source /home/centos/deploy/webapp/ccwebappenv/bin/activate
pip install -r /home/centos/deploy/webapp/requirements.txt 

sudo chown centos:centos /home/centos/webapp/ccwebappenv/
sudo chown centos:centos /home/centos/webapp/ccwebappenv/*
source /home/centos/deploy/webapp/ccwebappenv/bin/activate
pip install uwsgi flask
pip insatll Flask_Ext
