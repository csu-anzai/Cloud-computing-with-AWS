#!/usr/bin/python

from flask import (Flask, request, jsonify)
from flaskext.mysql import MySQL
import datetime
import bcrypt
import base64
import uuid
import os
from werkzeug.utils import secure_filename
import json
from password_strength import PasswordPolicy
import re
import boto3
from botocore.client import Config
import configparser
import logging
import logging.config
from logging.config import dictConfig
import mysql.connector
from mysql.connector import Error
import json
import statsd
from flask_statsdclient import StatsDClient
import time
from decimal import Decimal
from botocore.exceptions import ClientError

""" Config parser """
config = configparser.ConfigParser()
pathToConfig = "/home/centos/my.cnf"
config.read(pathToConfig)

""" Storing cofig variables in python variables """
local_run = config["Config"]['LOCAL_RUN']
aws_region = config["Config"]["AWS_REGION_NAME"]
production_run = config["Config"]['PRODUCTION_RUN']

""" A password policy """
policy = PasswordPolicy.from_names(
    length=8,
    uppercase=0,  # need min. 0 uppercase letters
    numbers=0,  # need min. 0 digits
    special=0,  # need min. 0 special characters
    nonletters=0,  # need min. 0 non-letter characters (digits, specials, anything)
    strength=0.1  # need a password that scores at least 0.3 with its strength
)

""" Set salt encoding beginning code"""
salt = b"$2a$12$w40nlebw3XyoZ5Cqke14M."

""" Initiate flask in app, db and statsd """
app = Flask("__name__")
db = MySQL()
c = StatsDClient(app)
db.init_app(app)

""" Initiate statsd """
app.config['STATSD_HOST'] = 'localhost'
app.config['STATSD_PORT'] = 8125
app.config['STATSD_PREFIX'] = 'statsd'

""" Initiate database """
if(production_run):
    logger.info("In production_run: %s", production_run)
    aws_s3_bucket_name = config["Config"]['S3_BUCKET_NAME']
    app.config['MYSQL_DATABASE_USER'] = 'csye6225master'
    app.config['MYSQL_DATABASE_PASSWORD'] = 'csye6225password'
    app.config['MYSQL_DATABASE_DB'] = 'csye6225'
    app.config['MYSQL_DATABASE_HOST'] = config["Config"]['RDS_INSTANCE']


elif(local_run):
    app.config['MYSQL_DATABASE_USER'] = "root"
    app.config['MYSQL_DATABASE_PASSWORD'] = 'password'
    app.config['MYSQL_DATABASE_DB'] = 'csye6225'
    app.config['MYSQL_DATABASE_HOST'] = 'localhost'

""" Logging config """
# LOGGING_CONFIG = None
logging.config.dictConfig({
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '{asctime} {levelname} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'default': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename' : '/opt/aws/amazon-cloudwatch-agent/logs/csye6225.log',
            'formatter': 'standard'
        },
    },
    'loggers': {
        '': {
            'handlers': ['default'],
            'propagate': True,
        }
    }
})

logger = logging.getLogger(__name__)
logger.setLevel("INFO")
 
''' IMAGES FOLDER PATH '''
UPLOAD_FOLDER = "/home/centos/deploy/Images/"


''' ALLOWED EXTENSIONS FOR UPLOAD ''' 
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg'])
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

""" Create secret key for UUID in database """
app.config['SECRET_KEY'] = 'my_key'
rds = config["Config"]['RDS_INSTANCE']    
dbUser = config["Config"]['MYSQL_DATABASE_USER']    
dbPass = config["Config"]['MYSQL_DATABASE_PASSWORD'] 
 
""" CREATE DB TABLES """   
rdsInstance = "-h"+rds
dataUser = "-u"+dbUser
dataPass = "-p"+dbPass

""" Connect to RDS instance """
try:
    connection = mysql.connector.connect(host=rds,
        user = dbUser,
        password = dbPass,
        database = 'csye6225',
        buffered=True)
    if connection.is_connected():
        logger.info("inside db $$$$$", connection.get_server_info())
except Error as e:
    logger.info("Error", e)



""" Create tables in Database """
def create_database():
    logger.info("Databse creation method initiated")
    cur = connection.cursor()
    logger.info("cursor", cur)
    cur.execute("show databases")
    cur.execute("CREATE table if not exists Person(id varchar(100) NOT NULL, username varchar(100) DEFAULT NULL, password varchar(100) DEFAULT NULL, PRIMARY KEY ( id ))")
    cur.execute("CREATE table if not exists Books(id varchar(100) NOT NULL, title varchar(50) DEFAULT NULL, author varchar(50) DEFAULT NULL, isbn varchar(50) DEFAULT NULL, quantity varchar(50) DEFAULT NULL, timeofcreation varchar(100), PRIMARY KEY ( id ))")
    cur.execute("CREATE table if not exists Image(id varchar(100) NOT NULL, url varchar(1000) DEFAULT NULL, book_id varchar(100) DEFAULT NULL, PRIMARY KEY ( id ))")
    logger.info("Tables created")
    
logger.info("Databse creation initiated")
create_database()
logger.info("Databse creation completed")
logger.info("Tables created")

""" UPLOAD IMAGE on S3 """
def upload_on_s3( filename , nameOfFile):
    try:
        s3 = boto3.client(
            "s3")
        bucket_resource = s3
        bucket_resource.upload_file(filename, aws_s3_bucket_name,nameOfFile)
        logger.info("UPLOAD SUCCESSFULL")
        logger.info("Image uploaded in s3")
        return True
    except ClientError as e:
        return e


""" DELETE IMAGE FROM S3 BUCKET """
def delete_image_from_s3( filename ):
    key_filename = filename
    logger.info("key_filename : ", key_filename)
    s3 = boto3.client(
        "s3")
    bucket_resource = s3
    logger.info("bucket_resource: %s", bucket_resource)
    try:

        s3.delete_object(
            Bucket = aws_s3_bucket_name,
            Key=key_filename)
        logger.info("deleted image from S3")
        logger.info("Image deleted from s3")            
    except Exception as e:
        logger.error("Exception in image deletion from s3: %s", e)
        logger.info("Exception : %s",e)

def presignedUrl( filename ):
    filename = filename
    logger.info("filename : %s", filename)
    s3_client = boto3.client('s3',
         config=Config(signature_version='s3v4'))
    logger.info("s3 client: %s", s3_client)
    try:
        logger.info("Bucket name:", aws_s3_bucket_name)
        resp_url = s3_client.generate_presigned_url(
            'get_object',
            Params = {
            'Bucket': aws_s3_bucket_name,
             'Key': filename,
             },
            ExpiresIn = 60*2
        )

        logger.info("resp_url:  %s", resp_url)
        logger.info("presigned url generated")
    except Exception as e:
        logger.error("Exception in presigned url generaiton:  %s", e)
        logger.info("Exception is:  %s", e)
    logger.info("Presigned url sent")
    return resp_url
    



""" REGISTER USER """
@app.route('/user/register', methods=['POST'])
def register_user():
    c.incr("register_user")
    logger.info("Registering for user")
    if request.authorization:
        logger.error("Auth headers found")
        c.incr("index_invalid_login")
        return jsonify("Auth headers found, cannot register"), 401
    try:
        if not request.content_type == 'application/json':
            return jsonify('failed', 'Content-type must be application/json', 401)
        try:
            email = request.json.get('username')
            logger.info("email : ",email)
            if not email:
                logger.error("Email not found")
                return jsonify("Email not found"), 400

            """ VERIFY EMAIL """
            is_valid = re.match('^[_a-z0-9-]+(\.[_a-z0-9-]+)*@[a-z0-9-]+(\.[a-z0-9-]+)*(\.[a-z]{2,4})$', email)
            if not is_valid:
                logger.error("Invalid email format")
                return jsonify("Bad email request"), 400

            """ VERIFY PASSWORD """
            myPassword = request.json.get('password')
            if not myPassword:
                logger.error("Password not found")
                return jsonify("Bad password"), 400

            """ CHECKING STRENGTH OF PASSWORD """
            if policy.test(myPassword):
                logger.error("Password not strong enough")
                return jsonify("Password not strong enough"), 400

            """ HASHING PASSWORD """
            password = bcrypt.hashpw(myPassword.encode('utf-8'), salt)
            logger.info("Password encrypted")

            """ CHECK IF USER EXISITS """
            conn = db.connect()
            logger.info("Connecting to database")
            cur = conn.cursor()
            logger.info("Creating cursor for database")

            cur.execute("SELECT * FROM Person where username=%s", email)
            logger.info("Fetching user details from database")
            user = cur.fetchone()

            if user is not None:
                logger.error("user already exists")
                return jsonify("User already exists"), 200


            """ ADDING USER TO DATABASE """
            cur.execute("INSERT INTO Person(id, username, password) VALUES (uuid(), %s, %s)", (email, password))
            logger.info("User registration successful")

            conn.commit()
            cur.close()
            logger.info("Database connection closed")
            c.incr("user_created")
            return jsonify('User registered successfully'), 200
        except Exception as e:
            logger.error("Exception:  %s", e)
            return jsonify(e), 500
    except Exception as e:
        logger.error("Exception:  %s", e)
        return jsonify(e), 400



""" ROUTE TO ROOT """
@app.route("/")
def index():
    c.incr("index")
    logger.info("User request auth")
    """ VERIFYING BASIC AUTH """
    if not request.authorization:
        logger.error("Email or password not entered")
        c.incr("index_invalid_login")
        return jsonify("Unauthorized"), 401

    username = request.authorization.username

    conn = db.connect()
    cur = conn.cursor()
    cur.execute("SELECT username, password FROM Person where username=%s", username)
    user = cur.fetchone()
    logger.info("user :", user)

    """ OBTAIN USERNAME AND PASSWORD BY TOKEN FROM DATABASE """
    if not user:
        logger.error("User does not exist in database")
        c.incr("index_invalid_login")
        return jsonify("Unauthorized"), 401

    userData = {}
    userData["username"] = user[0]
    userData["password"] = user[1]


    if request.authorization and request.authorization.username == userData["username"] and (bcrypt.checkpw(request.authorization.password.encode('utf-8'),userData["password"].encode('utf-8'))):
        cur.close()
        logger.info("User authenticated")
        c.incr("index_valid_login")
        return jsonify(str(datetime.datetime.now())), 200

    cur.close()
    logger.error("User credentials incorrect")
    c.incr("index_invalid_login")
    return jsonify("Unauthorized"), 401



""" REGISTER BOOK """
@app.route("/book", methods=["POST"])
def register_book():
    c.incr("register_book")
    logger.info("In api for registering book")
    try:
        """ AUTHENTICATE BY TOKEN """
        if not request.authorization:
            logger.error("Email or password not entered")
            c.incr("index_invalid_login")
            return jsonify("Unauthorized"), 401

        username = request.authorization.username

        conn = db.connect()
        cur = conn.cursor()
        cur.execute("SELECT username, password FROM Person where username=%s", username)
        user = cur.fetchone()
        logger.info("user :  %s", user)

        """ OBTAIN USERNAME AND PASSWORD BY TOKEN FROM DATABASE """
        if not user:
            logger.error("User does not exist in database")
            c.incr("index_invalid_login")
            return jsonify("Unauthorized"), 401

        userData = {}
        userData["username"] = user[0]
        userData["password"] = user[1]


        if request.authorization and request.authorization.username == userData["username"] and (bcrypt.checkpw(request.authorization.password.encode('utf-8'),userData["password"].encode('utf-8'))):
            cur.close()
            logger.info("User authenticated")
            c.incr("index_valid_login")            
            try:
                """ OBTAIN AND STORE BOOK DETAILS FROM JSON IN DATABSE """
                logger.info("Obtaining book data")

                book_data = request.get_json()
                logger.info("bookdata : %s", book_data)

                image_data = book_data['image']
                logger.info("imagedata  : %s", image_data)

                
                title = book_data['title']
                author = book_data['author']
                isbn = book_data['isbn']
                quantity = book_data['quantity']
                logger.info(" title : %s",title)
                logger.info(" author : %s",author)
                logger.info(" isbn : %s",isbn)

                book_id = image_data['id']
                url = image_data['url']
                logger.info(" book_id : %s", book_id)

                if not url:
                    if not book_id:
                        logger.info("no image deatilis")
                        conn = db.connect()
                        cur = conn.cursor()
                        try:

                            timeofcreation = get_current_time()
                            logger.info("timefocreation : %s", timeofcreation)
                            logger.info("returning info")
                            cur.execute("INSERT INTO Books(id, title, author, quantity, isbn, timeofcreation) VALUES(uuid(), %s, %s, %s, %s, %s)", (title, author, quantity, isbn, timeofcreation))
                            logger.info("query executed")
                            conn.commit()
                            logger.info("Book created in database")

                            cur.execute("SELECT * FROM Books order by timeofcreation desc")
                            book = cur.fetchone()
                            
                            cur.close()
                           
                            c.incr("book_registered")
                        except Exception as e:
                            logger.error("Exception in book register: %s", e)
                            return "Not posted"

                        

                """ DISPLAY BOOK DETAILS """
                bookData = {}
                logger.info("book retrieved from db :", book)
                bookData["id"] = book[0]
                bookData["title"] = book[1]
                bookData["author"] = book[2]
                bookData["isbn"] = book[3]
                bookData["quantity"] = book[4]
                bookData['Image'] = ''
                json1 = json.dumps(bookData, indent=4)

                image_array = {}
                image_array['book_id'] = ""
                image_array['url'] = ""
                logger.info("Image data for json", image_array)

                json2 = json.dumps(image_array, indent=4)
                logger.info("json2  %s", json2)
                resUm = json.loads(json1)
                logger.info (resUm)
                resUm['Image'] = json.loads(json2)
                logger.info("no ans")
                return json.dumps(resUm, indent=4), 200
            except Exception as e:
                logger.error("Exception in fetching book details:  %s", e)
                logger.info("in exception")
                logger.error("Book details not entered in proper format")
                c.incr("register_book_improper_format")
                return jsonify("Bad request"), 400
        logger.error("User not authenticated")
        c.incr("register_book_invalid_login")
        return jsonify("Unauthorized"), 401
    except Exception as e:
        logger.info("outer exception")
        logger.error("Exception in registering user:  %s", e)
        c.incr("register_book_invalid_login")
        return jsonify("Unauthorized"), 401

"""
GET BOOK BY ID
"""
@app.route("/book/<string:id>", methods=["GET"])
def request_a_book(id):
    c.incr("request_a_book")
    logger.info("Getting book by id")
    try:
        bookId = id
        logger.info("Book id obtained from header")

        """ AUTHENTICATE BY TOKEN """
        if not request.authorization:
            logger.error("Email or password not entered")
            c.incr("index_invalid_login")
            return jsonify("Unauthorized"), 401

        username = request.authorization.username

        conn = db.connect()
        cur = conn.cursor()
        cur.execute("SELECT username, password FROM Person where username=%s", username)
        user = cur.fetchone()
        logger.info("user :", user)

        """ OBTAIN USERNAME AND PASSWORD BY TOKEN FROM DATABASE """
        if not user:
            logger.error("User does not exist in database")
            c.incr("index_invalid_login")
            return jsonify("Unauthorized"), 401

        userData = {}
        userData["username"] = user[0]
        userData["password"] = user[1]


        if request.authorization and request.authorization.username == userData["username"] and (bcrypt.checkpw(request.authorization.password.encode('utf-8'),userData["password"].encode('utf-8'))):
            # cur.close()
            logger.info("User authenticated")
            c.incr("index_valid_login")
            try:
                cur.execute("SELECT id, title, author, isbn, quantity FROM Books where id=%s", bookId)
                book = cur.fetchone()

                if (book == None):
                    logger.error("Book not available in database")
                    c.incr("request_a_book_not_found")
                    return jsonify("Not found"), 404


                cur.execute("SELECT id, url FROM Image where book_id=%s", bookId)
                image = cur.fetchone()

                if image:
                    logger.info("Image obtained for book")
                    bookData = {}
                    bookData["id"] = book[0]
                    bookData["title"] = book[1]
                    bookData["author"] = book[2]
                    bookData["isbn"] = book[3]
                    bookData["quantity"] = book[4]
                    bookData['Image'] = ''
                    json1 = json.dumps(bookData, indent=4)

                    image_array = {}
                    image_array['id'] = image[0]
                    image_array['url'] = image[1]

                    json2 = json.dumps(image_array, indent=4)
                    resUm = json.loads(json1)
                    
                    resUm['Image'] = json.loads(json2)
                    return json.dumps(resUm, indent=4), 200
                else:
                    logger.info("Fetching book details")
                    bookData = {}
                    bookData["id"] = book[0]
                    bookData["title"] = book[1]
                    bookData["author"] = book[2]
                    bookData["isbn"] = book[3]
                    bookData["quantity"] = book[4]
                    bookData['Image'] = ''
                    json1 = json.dumps(bookData, indent=4)

                    image_array = {}
                    image_array['id'] = ''
                    image_array['url'] = ''

                    json2 = json.dumps(image_array, indent=4)
                    resUm = json.loads(json1)

                    resUm['Image'] = json.loads(json2)
                    logger.info("Book available to user")
                    c.incr("request_a_book_success")
                    return json.dumps(resUm, indent=4), 200
            except Exception as e:
                logger.error("User not authenticated")
                c.incr("request_a_book_fail")
                return jsonify("Unauthorized"), 401
    except Exception as e:
        logger.info("in exception")
        logger.error("Exception in fetching book by id:  %s", e)
        c.incr("request_a_book_fail")
        return jsonify("Unauthorized"), 401

"""
GET ALL BOOKS
"""
@app.route("/book", methods=["GET"])
def request_all_books():
    c.incr("request_all_books")
    logger.info("Requesting all books")
    try:
        """ AUTHENTICATE BY TOKEN """
        if not request.authorization:
            logger.error("Email or password not entered")
            c.incr("index_invalid_login")
            return jsonify("Unauthorized"), 401

        username = request.authorization.username

        conn = db.connect()
        cur = conn.cursor()
        cur.execute("SELECT username, password FROM Person where username=%s", username)
        user = cur.fetchone()
        logger.info("user :", user)

        """ OBTAIN USERNAME AND PASSWORD BY TOKEN FROM DATABASE """
        if not user:
            logger.error("User does not exist in database")
            c.incr("index_invalid_login")
            return jsonify("Unauthorized"), 401

        userData = {}
        userData["username"] = user[0]
        userData["password"] = user[1]


        if request.authorization and request.authorization.username == userData["username"] and (bcrypt.checkpw(request.authorization.password.encode('utf-8'),userData["password"].encode('utf-8'))):
            logger.info("User authenticated")
            c.incr("index_valid_login")
            cur.execute("SELECT * FROM Books")
            books = cur.fetchall()
            logger.info("All books fetched")
            logger.info(len(books))

            cur.execute("SELECT * FROM Image")
            img_es = cur.fetchall()
            logger.info("All images fetched")
            logger.info("len(img_es)  %s", len(img_es))

            output = []
            for book in books:
                if not img_es:
                    logger.info("No image in database")
                    logger.info("no images")
                    bookData = {}
                    bookData["id"] = book[0]
                    logger.info("Book 0", book[0])
                    bookData["title"] = book[1]
                    bookData["author"] = book[2]
                    bookData["isbn"] = book[3]
                    bookData["quantity"] = book[4]
                    bookData['Image'] = ''
                    json1 = json.dumps(bookData, indent=4)
                    logger.info("Books fetched")

                    image_array = {}
                    image_array["id"] = ''
                    image_array["url"] = ''
                    json2 = json.dumps(image_array, indent=4)
                    logger.info("Images fetched")

                    resUm = json.loads(json1)
                    resUm['Image'] = json.loads(json2)
                    jsonFile = json.dumps(resUm)
                    output.append(jsonFile)
                    logger.info("output:  %s",output)
            
                else:
                    for img in img_es:
                        logger.info("Obtaining Image")
                        bookData = {}
                        bookData["id"] = book[0]
                        bookData["title"] = book[1]
                        bookData["author"] = book[2]
                        bookData["isbn"] = book[3]
                        bookData["quantity"] = book[4]

                        bookData['Image'] = ''
                        json1 = json.dumps(bookData, indent=4)

                        if img[2]==book[0]:
                            logger.info("Obtaining book")
                            image_array = {}
                            image_array["id"] = img[0]
                            image_array["url"] = img[1]
                            logger.info("Image 1", img[1])
                            image_array["book_id"] = img[2]
                            json2 = json.dumps(image_array, indent=4)

                            resUm = json.loads(json1)

                            resUm['Image'] = json.loads(json2)
                            jsonFile = json.dumps(resUm)
                            output.append(jsonFile)

                            cur.close()
                            

                        else:
                            image_array = {}
                            image_array["id"] = ''
                            image_array["url"] = ''
                            json2 = json.dumps(image_array, indent=4)

                            resUm = json.loads(json1)
                            resUm['Image'] = json.loads(json2)
                            jsonFile = json.dumps(resUm, indent=4)
                            output.append(jsonFile)

                            cur.close()
                            
            logger.info("All books fetched")
            c.incr("request_all_books_success")
            return jsonify(output), 200
        logger.error("User not authenticated")
        c.incr("request_all_books_invalid_login")
        return jsonify("Unauthorized"), 401
    except Exception as e:
        logger.info("first try exception")
        logger.error("Exception in fetching all books:  %s", e)
        c.incr("request_all_books_invalid_login")
        return jsonify(e), 500

"""
UPDATE A BOOK
"""
@app.route("/book", methods=["PUT"])
def update_book():
    c.incr("update_book")
    logger.info("api for updating book")
    try:
        """ AUTHENTICATE BY TOKEN """
        if not request.authorization:
            logger.error("Email or password not entered")
            c.incr("index_invalid_login")
            return jsonify("Unauthorized"), 401

        username = request.authorization.username

        conn = db.connect()
        cur = conn.cursor()
        cur.execute("SELECT username, password FROM Person where username=%s", username)
        user = cur.fetchone()
        logger.info("user :", user)

        """ OBTAIN USERNAME AND PASSWORD BY TOKEN FROM DATABASE """
        if not user:
            logger.error("User does not exist in database")
            c.incr("index_invalid_login")
            return jsonify("Unauthorized"), 401

        userData = {}
        userData["username"] = user[0]
        userData["password"] = user[1]


        if request.authorization and request.authorization.username == userData["username"] and (bcrypt.checkpw(request.authorization.password.encode('utf-8'),userData["password"].encode('utf-8'))):
            logger.info("User authenticated")
            c.incr("index_valid_login")

            """ OBTAIN BOOK ID TO COMARE IN DATABASE """
            bookId = request.json.get("id")
            logger.info("id :  %s", bookId)

            if (bookId==None):
                logger.info("Book not entered")
                logger.info("Book not entered")
                return jsonify("Bad request"), 400
            """ OBTAIN BOOK BY ID """
            cur.execute("SELECT * FROM Books where id = %s", bookId)
            book = cur.fetchone()
            cur.close
            logger.info("book :  %s", book)

            if (book == None):
                logger.error("Book unavailable in database")
                return jsonify("No content"), 204

            cur = conn.cursor()

            cur.execute("SELECT * FROM Image where book_id=%s", bookId)
            image = cur.fetchone()
            try:

               book_data = request.get_json()
            except Exception as e:
                logger.error("Exception in fetching book:  %s", e)
                c.incr("update_book_invalid_login")
                return jsonify("Bad request"), 400

            sql_update_query = """UPDATE Books SET title=%s, author=%s, isbn=%s, quantity=%s where id=%s"""
            title = book_data['title']
            author = book_data['author']
            isbn = book_data['isbn']
            quantity = book_data['quantity']
            id = book_data['id']

            inputValues = (title, author, isbn, quantity, id)
            cur.execute(sql_update_query, inputValues)
            logger.info("Updating book data")

            conn.commit()

            cur.execute("SELECT * FROM Books where id=%s", book_data['id'])
            book = cur.fetchone()

            cur.execute("SELECT * FROM Image where book_id=%s", book_data['id'])
            image = cur.fetchone()


            """ DISPLAY BOOK DETAILS """
            bookData = {}
            bookData["id"] = book[0]
            bookData["title"] = book[1]
            bookData["author"] = book[2]
            bookData["isbn"] = book[3]
            bookData["quantity"] = book[4]
            bookData['Image'] = ''

            json1 = json.dumps(bookData, indent=4)

            image_array = {}
            if not image:
                image_array['id'] = ''
                image_array['url'] = ''

                json2 = json.dumps(image_array, indent=4)
                resUm = json.loads(json1)
                resUm['Image'] = json.loads(json2)
                logger.info("Book displayed to user")
                return json.dumps(resUm, indent=4), 200

            image_array['id'] = image[0]
            image_array['url'] = image[1]

            json2 = json.dumps(image_array, indent=4)
            resUm = json.loads(json1)
            resUm['Image'] = json.loads(json2)
            logger.info("Book displayed to user with image")
            c.incr("update_book_success")

            return json.dumps(resUm, indent=4), 200
        logger.error("User not authorized")
        c.incr("update_book_invalid_login")
        return jsonify("Unauthorized"), 401

    except Exception as e:
        logger.error("Exception in updating book:  %s", e)
        c.incr("update_book_invalid_login")
        return jsonify("Unauthorized"), 401

"""
DELETE A BOOK
"""
@app.route("/book/<string:id>", methods=["DELETE"])
def delete_book(id):
    c.incr("delete_book")
    logger.info("Deleting book")
    try:
        bookId = id

        if not request.authorization:
            logger.error("Email or password not entered")
            c.incr("index_invalid_login")
            return jsonify("Unauthorized"), 401

        username = request.authorization.username

        conn = db.connect()
        cur = conn.cursor()
        cur.execute("SELECT username, password FROM Person where username=%s", username)
        user = cur.fetchone()
        logger.info("user :", user)

        """ OBTAIN USERNAME AND PASSWORD BY TOKEN FROM DATABASE """
        if not user:
            logger.error("User does not exist in database")
            c.incr("index_invalid_login")
            return jsonify("Unauthorized"), 401

        userData = {}
        userData["username"] = user[0]
        userData["password"] = user[1]


        if request.authorization and request.authorization.username == userData["username"] and (bcrypt.checkpw(request.authorization.password.encode('utf-8'),userData["password"].encode('utf-8'))):
            logger.info("User authenticated")
            c.incr("index_valid_login")
            cur.execute("SELECT * FROM Image where book_id=%s", bookId)
            img_set =cur.fetchone()
            logger.info("logger.info img_set:  %s", img_set)

            imageUrl = img_set[1]
            logger.info("url: ",imageUrl)

            if not img_set:
                cur.execute("DELETE FROM Books WHERE id=%s", bookId)
                conn.commit()
                logger.info("Book without image deleted")
            else:
                """ DELETE BOOK FROM DATABASE """
                cur.execute("DELETE FROM Books WHERE id=%s", bookId)
                conn.commit()
                logger.info("Book alone deleted")

                cur.execute("DELETE FROM Image WHERE id=%s", img_set[0])
                conn.commit()
                logger.info("Book's image also deleted")

                ''' DELETING IMAGE FROM S3 IF EXISIS '''
                logger.info("Deleting book from s3")
                delete_image_from_s3(imageUrl)
                logger.info("Book deleted from s3")
            
            cur.close()
            return jsonify(''),204
        logger.error("User not authorized")
        c.incr("delete_book_invalid_login")
        return jsonify("Unauthorized"), 401
    except Exception as e:
        logger.error("Exception in deleting book:  %s ", e)
        c.incr("delete_book_invalid_login")
        return jsonify("Unauthorized"), 401

""" Upload book image """
@app.route('/book/<string:id>/image', methods=['POST'])
def upload_image(id):
    c.incr("upload_image")
    logger.info("Uploading book image")
    conn = db.connect()
    cur = conn.cursor()

    """ AUTHENTICATE BY TOKEN """
    if not request.authorization:
        logger.error("Email or password not entered")
        c.incr("index_invalid_login")
        return jsonify("Unauthorized"), 401

    username = request.authorization.username

    conn = db.connect()
    cur = conn.cursor()
    cur.execute("SELECT username, password FROM Person where username=%s", username)
    user = cur.fetchone()
    logger.info("user :", user)

    """ OBTAIN USERNAME AND PASSWORD BY TOKEN FROM DATABASE """
    if not user:
        logger.error("User does not exist in database")
        c.incr("index_invalid_login")
        return jsonify("Unauthorized"), 401

    userData = {}
    userData["username"] = user[0]
    userData["password"] = user[1]


    if request.authorization and request.authorization.username == userData["username"] and (bcrypt.checkpw(request.authorization.password.encode('utf-8'),userData["password"].encode('utf-8'))):
        logger.info("User authenticated")
        c.incr("index_valid_login")
        try:
            if 'file' in request.files:

                file = request.files['file']

                if file.filename == '':
                    logger.info("File not selected")
                    logger.info('No selected file')

                if file and allowed_file(file.filename):
                    logger.info("Verfiying file type")
                    filename = secure_filename(file.filename)
                    logger.info("File type verified")
                    logger.info("My filename:", filename)
                    logger.info("Saving file to folder")
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                    url_for_image = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    logger.info("File uploaded on local")
                    logger.info("Upload folder is:", UPLOAD_FOLDER)

                    """ OBTAIN BOOK ID TO COMPARE IN DATABASE """
                    bookId = id
                    logger.info("Book id fetched")
                    if (bookId == None):
                        logger.error("Book not available")
                        c.incr("upload_image_invalid_book_request")
                        return jsonify("Bad request"), 400

                    """ OBTAIN BOOK BY ID """
                    logger.info("Fetching book from database")
                    cur.execute("SELECT * FROM Books where id=%s", bookId)
                    book = cur.fetchone()
                    logger.info("Book fetched form database")

                    if (book == None):
                        logger.error("Book not found in database")
                        c.incr("upload_image_invalid_book_request")
                        return jsonify("No content"), 204
                    logger.info("Fetching book image")
                    cur.execute("SELECT * FROM Image WHERE book_id=%s", bookId)
                    image = cur.fetchone()
                    logger.info("Book image fetched")
                    logger.info("Image:", image)

                    if image is None:
                        logger.info("No image for book")
                        
                        logger.info("logger.infog **********")
                    else:
                        logger.info("image exists")
                        imageId = image[0]
                        logger.info("Deleting current book image")
                        cur.execute("DELETE FROM Image WHERE book_id=%s", bookId)
                        conn.commit()
                        logger.info("Deleting current book image successful")
                        logger.info("image deleted")
                        
                    logger.info("Inserting new book image")
                    cur.execute("INSERT INTO Image(id, url, book_id) VALUES (uuid(),%s, %s)", (url_for_image, bookId))
                    conn.commit()
                    logger.info("Inserting new book image successful")

                    '''upload image on S_3 bucket'''
                    # if production_run==True:
                    logger.info("Uploading book image to s3")
                    try:

                        upload_on_s3(url_for_image, filename)
                        
                        logger.info("UPLOAD SUCCESSFULL")
                        logger.info("Image uploaded in s3")
                    except ClientError as e:
                        return e
                    logger.info("Uploading book image to s3 successful")

                    """ OBTAIN IMAGE FROM IMAGE TABLE USING BOOKID And update Book table with the imageid"""
                    logger.info("Fetching book image from db")
                    cur.execute("SELECT * FROM Image where book_id=%s", bookId)
                    image = cur.fetchone()
                    logger.info("Book image fetched from db")

                    """ DISPLAY BOOK DETAILS """
                    bookData = {}
                    bookData["id"] = book[0]
                    bookData["title"] = book[1]
                    bookData["author"] = book[2]
                    bookData["isbn"] = book[3]
                    bookData["quantity"] = book[4]
                    bookData['Image'] = ''
                    json1 = json.dumps(bookData, indent=4)

                    image_array = {}
                    image_array['id'] = image[0]
                    image_array['url'] = image[1]

                    json2 = json.dumps(image_array, indent=4)
                    resUm = json.loads(json1)
                    resUm['Image'] = json.loads(json2)
 
                    cur.close()
                    logger.info("Book with image displayed")
                    c.incr("upload_image_success")

                    return json.dumps(resUm, indent=4), 201

        except Exception as e:
            logger.error("Exception in uploading book image:  %s", e)
            c.incr("upload_image_invalid_login")
            return jsonify(e), 500



"""
GET BOOK IMAGE
"""
@app.route("/book/<string:id>/image/<string:imgId>", methods=["GET"])
def get_book_image(id, imgId):
    c.incr("get_book_image")
    logger.info("Getting book image from id")
    try:
        logger.info("Getting book image")
        bookId = id
        logger.info("Book id obtained")
        # logger.info("BOOK ID", bookId)
        imageId = imgId
        logger.info("Image id obtained")

        logger.info("bookid: " + bookId + "img id: "+imageId)
        conn = db.connect()
        cur = conn.cursor()
        logger.info("conn establised")

        """ AUTHENTICATE BY TOKEN """
        if not request.authorization:
            logger.error("Email or password not entered")
            c.incr("index_invalid_login")
            return jsonify("Unauthorized"), 401

        username = request.authorization.username

        conn = db.connect()
        cur = conn.cursor()
        cur.execute("SELECT username, password FROM Person where username=%s", username)
        user = cur.fetchone()
        logger.info("user :", user)

        """ OBTAIN USERNAME AND PASSWORD BY TOKEN FROM DATABASE """
        if not user:
            logger.error("User does not exist in database")
            c.incr("index_invalid_login")
            return jsonify("Unauthorized"), 401

        userData = {}
        userData["username"] = user[0]
        userData["password"] = user[1]


        if request.authorization and request.authorization.username == userData["username"] and (bcrypt.checkpw(request.authorization.password.encode('utf-8'),userData["password"].encode('utf-8'))):
            # cur.close()
            logger.info("User authenticated")
            c.incr("index_valid_login")
            # return jsonify(str(datetime.datetime.now())), 200
            try:
                """ OBTAIN BOOK BY ID from local db"""
                cur.execute("SELECT * FROM Image where id=%s and book_id=%s", (imageId, bookId))
                image = cur.fetchone()
                logger.info("MYIMAGE", image)
                logger.info("Image fetched from database")

                output = []
                image_data = {}
                image_data["id"] = image[0]
                image_data["url"] = image[1]

                # if(local_run==True):
                #     logger.info("IN LOCAL RUN")
                #     output.append(image_data)
                #     cur.cose()
                #     return jsonify(output),200
                # else:
                logger.info("IN PRESIGNED URL")
                logger.info("my urls is", image_data["url"])
                url_pre = str(image_data["url"])
                modified_url = presignedUrl(url_pre)
                logger.info("url", modified_url)
                image_data["url"] = modified_url
                logger.info("image data url", image_data["url"])
                output.append(image_data)
                logger.info("Image details displayed to user")
                c.incr("get_book_image_success")
                return jsonify(output),200
            except Exception as e:
                return jsonify(e), 401

            


        cur.close()
        logger.info("Database connection closed")
        logger.error("Invalid login information")
        c.incr("get_book_image_invalid_login")
        return jsonify("Unauthorized"), 401
    except Exception as e:

        logger.info("in exception  %s", e)
        logger.error("Exception in fetching image details:  %s", e)
        c.incr("get_book_image_invalid_login")
        return jsonify("Unauthorized"), 401



""" UPDATE BOOK IMAGE """
@app.route("/book/<string:id>/image/<string:imgId>", methods=["PUT"])
def update_image(id, imgId):
    c.incr("update_image")
    logger.info("Updating book image")
    bookId = id
    logger.info("Book id obtained")
    imageId = imgId
    logger.info("Image id obtained")

    conn = db.connect()
    cur = conn.cursor()
    logger.info("Database connection establised")

    """ AUTHENTICATE BY TOKEN """
    if not request.authorization:
        logger.error("Email or password not entered")
        c.incr("index_invalid_login")
        return jsonify("Unauthorized"), 401

    username = request.authorization.username

    conn = db.connect()
    cur = conn.cursor()
    cur.execute("SELECT username, password FROM Person where username=%s", username)
    user = cur.fetchone()
    logger.info("user :  %s", user)

    """ OBTAIN USERNAME AND PASSWORD BY TOKEN FROM DATABASE """
    if not user:
        logger.error("User does not exist in database")
        c.incr("index_invalid_login")
        return jsonify("Unauthorized"), 401

    userData = {}
    userData["username"] = user[0]
    userData["password"] = user[1]


    if request.authorization and request.authorization.username == userData["username"] and (bcrypt.checkpw(request.authorization.password.encode('utf-8'),userData["password"].encode('utf-8'))):
        # cur.close()
        logger.info("User authenticated")
        c.incr("index_valid_login")
        # return jsonify(str(datetime.datetime.now())), 200
        if not request.json:
            logger.error("Bad json format")
            c.incr("update_image_invalid_format")
            return jsonify("Bad request"), 400

        try:
            logger.info ("in upload_image")

            if 'file' in request.files:
                logger.info("file present")

                file = request.files['file']
                logger.info (file.filename)

                if file.filename == '':
                    logger.info("No file selected")
                    logger.info('No selected file')

                if file and allowed_file(file.filename):
                    logger.info("Checking file format")
                    filename = secure_filename(file.filename)
                    logger.info("File format valid")

                    logger.info("filename: ",filename)
                    logger.info("Saving image in folder")
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                    url_for_image = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    logger.info("File saved in local folder")

                    logger.info("url: ", url_for_image)

                    """ OBTAIN BOOK ID TO COMPARE IN DATABASE """
                    bookId = id
                    if (bookId == None):
                        logger.error("Book id not available")
                        c.incr("update_image_bad_request")
                        return jsonify("Bad request"), 400

                    """ OBTAIN BOOK BY ID """
                    cur.execute("SELECT * FROM Books WHERE id=%s", bookId)
                    book = cur.fetchone()
                    logger.info("book:  %s ", book)
                    logger.info("Book fetched from database")

                    if (book == None):
                        logger.info("no book")
                        logger.error("Book not available in database")
                        c.incr("update_image_bad_request")
                        return jsonify("No content"), 204

                    cur.execute("SELECT * FROM Image WHERE id=%s", imageId)
                    imageDb = cur.fetchone()
                    logger.info("Image fetched from database")

                    if imageDb:
                        logger.info("Updating book image")
                        cur.execute("UPDATE Image SET url=%s WHERE book_id=%s", (url_for_image, bookId))
                        conn.commit()
                        cur.close()
                        logger.info("Book image updated")

                    # else:
                        # return jsonify('Cannot update'), 204
                logger.info("Updating book image successful")
                c.incr("update_image_success")
                return jsonify('No Content'),204
            logger.info("Updating book image details")
            return json.dumps(resUm, indent=4), 201
        except Exception as e:
            logger.error("Exception in updating book image:  %s", e)
            c.incr("update_image_invalid_login")
            return jsonify(e), 500

"""
DELETE A IMAGE
"""
@app.route("/book/<string:id>/image/<string:imgId>", methods=["DELETE"])
def delete_image(id, imgId):
    c.incr("delete_image")
    logger.info("Deleting book image")
    try:
        bookId = id
        logger.info("Book id fetched")
        imageId = imgId
        logger.info("Image id fetched")

        conn = db.connect()
        cur = conn.cursor()

        """ AUTHENTICATE BY TOKEN """
        if not request.authorization:
            logger.error("Email or password not entered")
            c.incr("index_invalid_login")
            return jsonify("Unauthorized"), 401

        username = request.authorization.username

        conn = db.connect()
        cur = conn.cursor()
        cur.execute("SELECT username, password FROM Person where username=%s", username)
        user = cur.fetchone()
        logger.info("user : %s", user)

        """ OBTAIN USERNAME AND PASSWORD BY TOKEN FROM DATABASE """
        if not user:
            logger.error("User does not exist in database")
            c.incr("index_invalid_login")
            return jsonify("Unauthorized"), 401

        userData = {}
        userData["username"] = user[0]
        userData["password"] = user[1]


        if request.authorization and request.authorization.username == userData["username"] and (bcrypt.checkpw(request.authorization.password.encode('utf-8'),userData["password"].encode('utf-8'))):
            # cur.close()
            logger.info("User authenticated")
            c.incr("index_valid_login")
            """ OBTAIN BOOK BY ID """
            # cur.execute("SELECT * FROM Books WHERE id=bookId")
            # book = cur.fetchone()
            cur.execute("SELECT * FROM Image WHERE id=%s", imgId)
            image = cur.fetchone()
            logger.info("Image fetched from database")
            logger.info("image : %s", image)
            imageUrl = image[1]

            if (image == None):
                logger.info("Image not in database")
                c.incr("delete_image_not_found")
                return jsonify("No content"), 204

            # if (book == None):
            #     return jsonify("No content"), 204

            logger.info("image book id : ", image[2])
            logger.info("book book id : ", bookId)

            if image[2] == bookId:
                logger.info("in if")

                """ DELETE Image FROM DATABASE """
                logger.info("Deleting book image from database")
                cur.execute("DELETE FROM Image WHERE id=%s", image[0])
                conn.commit()
                cur.close()
                logger.info("Deleting book image successful")

                # if not local_run:
                ''' DELETING IMAGE FROM S3 IF EXISIS '''
                logger.info("Deleting book image form s3")
                delete_image_from_s3(imageUrl)
                logger.info("Deleting book image from s3 successful")

            logger.info("Deleting book image successful")
            c.incr("delete_image_success")
            return jsonify('No Content'),204
        logger.error("Invalid user information")
        c.incr("delete_image_invalid_login")
        return jsonify("Unauthorized"), 401
    except Exception as e:
        logger.info("exception : ", e)
        logger.error("Exception in deleting book image:  %s", e)
        c.incr("delete_image_invalid_login")
        return jsonify("Unauthorized"), 401
#Parameters for sending email
SUBJECT = "Reset password"
DOMAIN_NAME = config["Config"]['DOMAIN_NAME']
# newDomain = DOMAIN_NAME.rstrip(".")
newDomain = DOMAIN_NAME
SENDER = newDomain


def generate_reset_Link(domain_name, email, token):
    #Parameters for sending email
    SUBJECT = "Reset password"
    DOMAIN_NAME = config["Config"]['DOMAIN_NAME']
    # newDomain = DOMAIN_NAME.rstrip(".")
    newDomain = DOMAIN_NAME
    SENDER = newDomain
    resetLink = "https://"+domain_name+"/reset@email="+email+"&token="+token
    return resetLink

def send_Email(email, resetLink):
    logger.info("Sending email to SNS")
    try:  
        client = boto3.client('ses',region_name='us-east-1')
        logger.info("sending email client created")
        client.send_email(
            Source = SENDER,
            Destination = {
                'ToAddresses': [
                    email
                ]
            },
            Message = {
                'Subject': {
                    'Data': SUBJECT
                },
                'Body': {
                    'Html': {
                        'Data': '<html><head>'
                        + '<meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />'
                        + '<title>' + SUBJECT + '</title>'
                        + '</head><body>'
                        + 'Please <a href="' + resetLink + '">click here to reset your email address</a> or copy & paste the following link in a browser:'
                        + '<br><br>'
                        + '<a href="' + resetLink + '">' + resetLink + '</a>'
                        + '</body></html>'
                    }
                }
            })
        logger.info("Client is sending email")
    
        c.incr('api.passwordReset.POST.200')
        return jsonify({"message": " : you will receive password reset link if the email address exists in our system"})
    except Exception as e:
        logger.info("Exception oin sending email:  %s", e)
        c.incr('api.passwordReset.POST.400')
        return jsonify({"message": " : you will receive password reset link if the email address exists in our system"})

def generate_uuid():
    ur_uuid = uuid.uuid4()
    logger.info("My weird string: %s", ur_uuid)
    logger.info("My weird strings type: %s", ur_uuid)
    return str(ur_uuid)

def generate_time_for_dynamoDB():
    logger.info("Getting time for dynamodb")
    dynamotime = Decimal(time.time() + 900)
    logger.info("Got dynamo time: %s", dynamotime)
    return dynamotime

def get_current_time():
    logger.info("Getting current time")
    try:
        ctime = Decimal(time.time())
        logger.info("Got current time: %s", ctime)
        return ctime
    except Exception as e:
        logger.error("Exception is %s", e)
        return time.time()


def get_record_from_dynamodb(table, email):
    logger.info("get records from dynamo: %s ,%s", table, email)
    response = table.get_item(
        
            Key={

                'id':email
            }
        )
    return response

def put_record_in_dynamodb(table, email, myuuid, expiryTime):
    response = table.put_item(
        Item={

        "id": email,
        "token": myuuid,
        "ttlDynamo":expiryTime

        })
    return response

def get_record_details(email):
    logger.info("getting token from dynamodb...")

    # Get the service resource.
    dynamodb = boto3.resource('dynamodb', region_name=aws_region)
    logger.info("Dynamo db client created")

    table = dynamodb.Table('csye6225')
    logger.info("Dynamo db table is: %s", table)

    try:
        #get record exists in dynamodb
        response = get_record_from_dynamodb(table, email)
        logger.info("First get response:  %s", response)

        for (key, value) in response.items():
       # Check if key is even then add pair to new dictionary
            if key == "Item":
                item = response['Item']
                ttlTimeInDynamoDB = item['ttlDynamo']
                currentTime = get_current_time()

                logger.info("ttlTimeInDynamoDB :  %s", ttlTimeInDynamoDB)
                logger.info("currentTime : %s ", currentTime)

                if currentTime > ttlTimeInDynamoDB:
                    resDict = {}
                    resDict['msg'] = "Send email"
                    resDict['details'] = item
                    # resJson = json.dumps(resDict, indent=4)
                    logger.info("resJson =  %s", resDict)
                else:
                    resDict = {}
                    resDict['msg'] = "Do not send email"
                    resDict['details'] = ""
                    # resJson = json.dumps(resDict)
                    logger.info("resJson =  %s", resDict)
                
                return resDict
            else:
                output = "None returmed"
                myUuid = generate_uuid()
                expiryTime = generate_time_for_dynamoDB()

                put_record_in_dynamodb(table, email, myUuid, expiryTime)
                
                newRes = get_record_from_dynamodb(table, email)
                logger.info("New response:  %s", newRes)

                for (key, value) in newRes.items():
               # Check if key is even then add pair to new dictionary
                    if key == "Item":
                        item = newRes['Item']
                        logger.info("GetItem succeeded:")
                        logger.info(item)
                        resDict = {}
                        resDict['msg'] = "Send email"
                        resDict['details'] = item
                        # logger.info("else dumps")
                        # resJson = json.dumps(resDict)
                        logger.info("resJson = ", resDict)

                        return resDict
        # return item

    except ClientError as e:
        logger.info(e.response['Error']['Message'])


@app.route("/reset", methods=["POST"])
def reset_password():
    c.incr('api.passwordReset')
    try:

        email=request.json.get("username")
        logger.info("username:  %s",email)

        #Get emailId and verify if it exists in db
        if (email == ""):
            logger.debug("email is empty")
            return jsonify({'message': 'Email cant be empty'}, status=400)
        
        #verrsify if username is valid
        email_status = verifyUsername(str(email))
        logger.info("username verified")

        try:
            conn = db.connect()
            cur = conn.cursor()

            cur.execute("select * from Person where username=%s", email)
            user = cur.fetchone()

            if email_status is not None:
                if user:
                    respDict = get_record_details(email)
                    # respJson = json.loads(respDict)

                    # logger.info("response msg : ",respJson)
                    # logger.info("response msg : ",respJson['msg'])
                    responseMsg = respDict['msg']
                    responseDetails = respDict['details']

                    if responseMsg == "Send email":

                            logger.info("My token is",responseDetails['token'])
                            token = responseDetails['token']

                            #generate password reset link
                            resetLink = generate_reset_Link(newDomain, email, token)
                            logger.info("Reset link is:", resetLink)

                            #send email
                            send_Email(email, resetLink)

                            return jsonify("Email sent successfully"), 200
                    else:
                        return jsonify("Check email for password reset"), 200  
                else:
                    return jsonify ("User does not exist"), 400
            else:
                return jsonify("Invalid userId"), 400
        except Error as e:
            return jsonify(e), 400
    except Exception as e:
        return jsonify(e), 400

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def shutdown_server():
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()
<<<<<<< HEAD
def verifyUsername(email):
    is_valid = re.match('^[_a-z0-9-]+(\.[_a-z0-9-]+)*@[a-z0-9-]+(\.[a-z0-9-]+)*(\.[a-z]{2,4})$', email)
    logger.info("Is valid email?", is_valid)
    return is_valid
=======
>>>>>>> parent of f7f960c... verify username

@app.route('/shutdown', methods=['GET'])
def shutdown():
    shutdown_server()
    return 'Server shutting down...'

""" RUN FLASK APP """
if __name__ == '__main__':
    app.run(host='0.0.0.0')
