
sudo chown centos:centos /home/centos/deploy/webapp
sudo chown -R centos:centos /home/centos/deploy/webapp/*

sudo semanage permissive -a httpd_t
setsebool -P httpd_can_network_connect true
sudo scl enable rh-python36 "virtualenv /home/centos/deploy/webapp/ccwebappenv"

sudo scl enable rh-python36 "source /home/centos/deploy/webapp/ccwebappenv/bin/activate"
sudo scl enable rh-python36 "pip install -r /home/centos/deploy/webapp/requirements.txt" 

sudo chown centos:centos /home/centos/webapp/ccwebappenv/
sudo chown centos:centos /home/centos/webapp/ccwebappenv/*
sudo scl enable rh-python36 "source /home/centos/deploy/webapp/ccwebappenv/bin/activate"
sudo scl enable rh-python36 "pip install uwsgi flask"
sudo scl enable rh-python36 "pip insatll Flask_Ext"
sudo scl enable rh-python36 "pip install mysql-connector-python"
