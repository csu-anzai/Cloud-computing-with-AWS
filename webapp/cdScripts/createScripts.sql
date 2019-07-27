show databases;
use csye6225;

drop table if exists Books;
drop table if exists Image;
drop table if exists Person;

CREATE TABLE Books(
  id varchar(100) NOT NULL,
  title varchar(50) DEFAULT NULL,
  author varchar(50) DEFAULT NULL,
  isbn varchar(50) DEFAULT NULL,
  quantity varchar(50) DEFAULT NULL,
  PRIMARY KEY ( id )
);


CREATE TABLE Image(
  id varchar(100) NOT NULL,
  url varchar(1000) DEFAULT NULL,
  book_id varchar(100) DEFAULT NULL,
  PRIMARY KEY ( id )
);


CREATE TABLE Person(
  id varchar(100) NOT NULL,
  username varchar(100) DEFAULT NULL,
  password varchar(100) DEFAULT NULL,
  PRIMARY KEY ( id )
);
