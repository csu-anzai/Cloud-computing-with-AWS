#!/usr/bin/bash -xe
echo "anuja"
echo $PATH
echo ${RDS_INSTANCE}
eval ${RDS_INSTANCE}
cd /home/centos/deploy/webapp
sudo virtualenv flaskEnv
source flaskEnv/bin/activate
source /home/centos/deploy/infrastructure/aws/codedeploy/my.config
echo $rds
echo RDS has value ${rds}
sudo mysql -h${rds} -u${MYSQL_DATABASE_USER} -p${MYSQL_DATABASE_PASSWORD} < /home/centos/deploy/createScripts.sql
