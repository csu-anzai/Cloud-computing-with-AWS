#!/usr/bin/bash
echo "anuja"
echo $PATH
echo ${RDS_INSTANCE}

cd /home/centos/deploy/webapp
virtualenv flaskEnv
source flaskEnv/bin/activate
pip3.6 install -r requirements.txt

sudo mysql -h${RDS_INSTANCE} -u${MYSQL_DATABASE_USER} -p${MYSQL_DATABASE_PASSWORD} < /home/centos/deploy/createScripts.sql
