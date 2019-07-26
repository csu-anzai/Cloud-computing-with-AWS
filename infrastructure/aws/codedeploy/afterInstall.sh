sudo mysql -h $RDS_INSTANCE -P $DATABASE_PORT -u  $MYSQL_DATABASE_USER -p $MYSQL_DATABASE_PASSWORD < /home/centos/deploy/createScripts.sql
