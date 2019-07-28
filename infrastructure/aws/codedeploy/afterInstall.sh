#!/usr/bin/bash
echo "anuja"
echo $PATH
echo ${RDS_INSTANCE}

cd /home/centos/deploy/webapp
sudo virtualenv flaskEnv
source flaskEnv/bin/activate

sudo mysql -h ${RDS_INSTANCE} -u ${MYSQL_DATABASE_USER} < /home/centos/deploy/createScripts.sql
