
# rds_instance=$RDS_INSTANCE
dbName="csye6225"
# if [ $MYSQL_DATABASE_PASSWORD ]
# then
mysql -h$RDS_INSTANCE -P 3306 -u$MYSQL_DATABASE_USER -p$MYSQL_DATABASE_PASSWORD -e "show databases;"
#   else
#   mysql -u "$MYSQL_DATABASE_USER" -e "SHOW DATABASES"
# fi
# if [ $MYSQL_DATABASE_USER ]
# then
# mysql -h$RDS_INSTANCE -P 3306 -u$MYSQL_DATABASE_USER -p$MYSQL_DATABASE_PASSWORD 
# mysql -h$RDS_INSTANCE -P 3306 -u$MYSQL_DATABASE_USER -p$MYSQL_DATABASE_PASSWORD -e "use csye6225;"
# else
#   mysql -u "$MYSQL_DATABASE_USER" -e "SHOW DATABASES"
# fi
# if [ $MYSQL_DATABASE_PASSWORD ]
# then
mysql -h${RDS_INSTANCE} -P 3306 -u$MYSQL_DATABASE_USER -p$MYSQL_DATABASE_PASSWORD -e <<mysqlscript
CREATE TABLE Books (id varchar(100) NOT NULL, title varchar(50) DEFAULT NULL, author varchar(50) DEFAULT NULL, isbn varchar(50) DEFAULT NULL, quantity varchar(50) DEFAULT NULL, PRIMARY KEY (id));
mysqlscript

mysql -h$RDS_INSTANCE -P 3306 -u$MYSQL_DATABASE_USER -p$MYSQL_DATABASE_PASSWORD -e "desc Books;"
# else
#   mysql -u "$MYSQL_DATABASE_USER" -e "SHOW DATABASES"
# fi
# if [ $MYSQL_DATABASE_PASSWORD ]
# then
# mysql -h${RDS_INSTANCE} -P 3306 -u$MYSQL_DATABASE_USER -p$MYSQL_DABASE_PASSWORD -e "CREATE TABLE Books (
#   id varchar(100) NOT NULL,
#   title varchar(50) DEFAULT NULL,
#   author varchar(50) DEFAULT NULL,
#   isbn varchar(50) DEFAULT NULL,
#   quantity varchar(50) DEFAULT NULL,
#   PRIMARY KEY (id)
# );"
# else
#   mysql -u "$MYSQL_DATABASE_USER" -e "SHOW DATABASES"
# fi

# if [ $MYSQL_DATABASE_PASSWORD ]
# then
# mysql -h${RDS_INSTANCE} -P 3306 -u$MYSQL_DATABASE_USER -p$MYSQL_DATABASE_PASSWORD -e <<MYSQL_SCRIPT
# CREATE TABLE "Image" ("id" varchar(100) NOT NULL,"url" varchar(1000) DEFAULT NULL,"book_id" varchar(100) DEFAULT NULL,PRIMARY KEY ("id"));
# MYSQL_SCRIPT
# else
#   mysql -u "$MYSQL_DATABASE_USER" -e "SHOW DATABASES"
# fi

# if [ $MYSQL_DATABASE_PASSWORD ]
# then
# mysql -h${RDS_INSTANCE} -P 3306 -u$MYSQL_DATABASE_USER -p$MYSQL_DATABASE_PASSWORD -e "CREATE TABLE "Person" (
#   "id" varchar(100) NOT NULL,
#   "username" varchar(100) DEFAULT NULL,
#   "password" varchar(100) DEFAULT NULL,
#   PRIMARY KEY ("id")
# );"
# else
#   mysql -u "$MYSQL_DATABASE_USER" -e "SHOW DATABASES"
# fi
# if [ $MYSQL_DATABASE_PASSWORD ]
# then
# mysql -h${RDS_INSTANCE} -P 3306 -u$MYSQL_DATABASE_USER -p$MYSQL_DATABASE_PASSWORD -e "FLUSH PRIVILEGES;"
# else
#   mysql -u "$MYSQL_DATABASE_USER" -e "SHOW DATABASES"
# fi

# if [ $MYSQL_DATABASE_PASSWORD ]
# then
# 	mysql -h${RDS_INSTANCE} -P 3306 -u$MYSQL_DATABASE_USER -p$MYSQL_DATABASE_PASSWORD -e "exit"
# else
#   mysql -u "$MYSQL_DATABASE_USER" -e "SHOW DATABASES"
# fi
