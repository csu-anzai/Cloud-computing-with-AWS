sudo mysql -h $RDS_INSTANCE -u  $MYSQL_DATABASE_USER -p $MYSQL_DATABASE_PASSWORD -P $DATABASE_PORT < /home/centos/deploy/createScripts.sql
