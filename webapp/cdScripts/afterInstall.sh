echo $RDS_INSTANCE
sudo mysql -h$RDS_INSTANCE -u $MYSQL_DATABASE_USER -p$MYSQL_DATABASE_PASSWORD --databse csye6225 < /home/centos/webapp/cdScripts/createScripts.sql

#echo "show databases" | mysql -u $MYSQL_DATABASE_USER -h$RDS_INSTANCE -p $MYSQL_DATABASE_PASSWORD
#< /home/centos/webapp/cdScripts/createScripts.sql
