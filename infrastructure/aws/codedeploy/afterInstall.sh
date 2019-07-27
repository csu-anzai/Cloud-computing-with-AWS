echo "anuja"
echo $PATH
echo $RDS_INSTANCE


sudo mysql -h $RDS_INSTANCE -u  $MYSQL_DATABASE_USER -p $MYSQL_DATABASE_PASSWORD -P 3306 < /home/centos/deploy/createScripts.sql
