#!/usr/bin/bash -xe
echo "anuja"
echo $PATH
echo ${RDS_INSTANCE}
eval ${RDS_INSTANCE}
cd /home/centos/deploy/webapp
sudo virtualenv flaskEnv
source flaskEnv/bin/activate
source /home/centos/my.cnf
echo $RDS_INSTANCE
echo RDS has value ${RDS_INSTANCE}
sudo mysql -h${RDS_INSTANCE} -u${MYSQL_DATABASE_USER} -p${MYSQL_DATABASE_PASSWORD} < /home/centos/deploy/createScripts.sql
