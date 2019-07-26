sudo mysql -h $RDS_INSTANCE --port=3306 -u  $MYSQL_DATABASE_USER -p $MYSQL_DATABASE_PASSWORD < /home/centos/deploy/createScripts.sql
